from robot.src.MovementDecoder import BoardPositions
from robot.src.MovementManager import MovementManager, decode_movement, orientation_position
from robot.src.gripper import GripperManager

class Robot:
    def __init__(self, host, port, gripper_test_mode=False):
        self.gm = GripperManager(host=host, port=port, test_mode=gripper_test_mode)
        self.bp = BoardPositions(x0=0.43646, y0=-0.2545, x7=0.15070, y7=0.02702)
        self.posManager = MovementManager()
        self.gm.send_command(f"set_tcp(p[0.0,0.0,0.2286,0.0,0.0,0.0])\n")

        # self.original_joint = [0.0401425728, -1.5613715488, -1.4295991903, -1.7366026057, -4.7193702974, 0.028099801]
        # self.original_pose_coord  = [0.29370, 0.16464] # [0.293694398621, -0.122202442352]
        self.original_joint = [-0.6928957, -1.88827172, -0.99413954, -1.83538824, -4.72896961, 0.028099801]
        self.original_pose_coord  = [0.19331, -0.33896] # [0.293694398621, -0.122202442352]

        self.box_coord = [0.19331, -0.33896] # [0.29370, 0.16464]
        self.box_orient = [2.220, -2.197, -0.009]

        self._initial_position()
        self.gm.open_gripper()

    def _initial_position(self):
        # orientation = orientation_position(None, None)[0]
        orientation = self.box_orient
        self.gm.move_robot(self.original_pose_coord, orientation, 'up', self.original_joint, wait_time=2.5)
        # self.gm.move_robot(self.original_pose_coord, orientation, 'up')

    def move_piece(self, movement, return_initial_position=True, checkmate=False, is_pawn=False):
        
        # self._initial_position()

        if not is_pawn:
            type_down_take = 'down_take'
            type_down_leave = 'down_leave'
        else:
            type_down_take = 'down_take_pawn'
            type_down_leave = 'down_leave_pawn'

        # Extract position and orientations
        position = self.bp.decode_move(movement)
        q_init, q_final, orientation_init, orientation_final = self.posManager.qs_orient_position(movement)
        orientation_init, orientation_final = self.posManager.winning_orientation_position(movement)

        # Move to first position of the movement: up, down, take chess piece, up
        self.gm.move_robot([position[0], position[1]], orientation_init, 'up', q_init, wait_time=2.5)
        # self.gm.open_gripper()
        self.gm.move_robot([position[0], position[1]], orientation_init, type_down_take, q_init, wait_time=2.5)

        # Take piece
        self.gm.close_gripper()
        self.gm.move_robot([position[0], position[1]], orientation_init, 'up', q_init)

        # Move to second position of the movement: up, down, leave chess piece, up
        self.gm.move_robot([position[2], position[3]], orientation_final, 'up', q_final, checkmate=checkmate)
        self.gm.move_robot([position[2], position[3]], orientation_final, type_down_leave, q_final, wait_time=2.5)
        
        # Leave piece
        self.gm.open_gripper()
        self.gm.move_robot([position[2], position[3]], orientation_final, 'up', q_final)
        # self.gm.close_gripper()

        if return_initial_position:
            self._initial_position()

        # if not checkmate:

        #     # Move to second position of the movement: up, down, leave chess piece, up
        #     self.gm.move_robot([position[2], position[3]], orientation_final, 'up', q_final)
        #     self.gm.move_robot([position[2], position[3]], orientation_final, 'down_leave', q_final, wait_time=2.5)
            
        #     # Leave piece
        #     self.gm.open_gripper()
        #     self.gm.move_robot([position[2], position[3]], orientation_final, 'up', q_final)
        #     self.gm.close_gripper()
        #     self._initial_position()

        # else:

        #     # Move to second position of the movement to drop the piece
        #     self.gm.move_robot([position[2], position[3]], orientation_final, 'up', q_final, checkmate=True)


    def capture_piece(self, movement, is_checkmate=False, is_pawn=False):
        # self._initial_position()

        if not is_pawn:
            type_down_take = 'down_take'
            type_down_leave = 'down_leave'
        else:
            type_down_take = 'down_take_pawn'
            type_down_leave = 'down_leave_pawn'

        # Extract position and orientations
        position = self.bp.decode_move(movement)
        q_init, q_final, orientation_init, orientation_final = self.posManager.qs_orient_position(movement)
        orientation_init, orientation_final = self.posManager.winning_orientation_position(movement)

        if is_checkmate:
            self.move_piece(movement, checkmate=True)

        else:

            # Move to last position of the movement to remove the target piece: up, down, take chess piece, up
            self.gm.move_robot([position[2], position[3]], orientation_final, 'up', q_final)
            # self.gm.open_gripper()
            self.gm.move_robot([position[2], position[3]], orientation_final, type_down_take, q_final, wait_time=2)

            # Take piece
            self.gm.close_gripper()
            self.gm.move_robot([position[2], position[3]], orientation_final, 'up', q_final)          

            ############################################################################################################
            # TODO: Mode to the dummy box
            # Move to the dummy box
            self.gm.move_robot(self.box_coord, self.box_orient, 'up', wait_time=3.5)
            self.gm.open_gripper()
            ############################################################################################################