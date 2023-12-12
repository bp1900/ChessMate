from robot.src.MovementDecoder import BoardPositions
from robot.src.MovementManager import MovementManager, decode_movement, orientation_position
from robot.src.gripper import GripperManager

class Robot:
    def __init__(self):
        self.gm = GripperManager()
        self.bp = BoardPositions(x0=0.43646, y0=-0.2545, x7=0.15070, y7=0.02702)
        self.posManager = MovementManager()
        self.gm.send_command(f"set_tcp(p[0.0,0.0,0.2286,0.0,0.0,0.0])\n")

        self.original_joint = [0.0401425728, -1.5613715488, -1.4295991903, -1.7366026057, -4.7193702974, 0.028099801]
        self.original_pose_coord  = [0.293694398621, -0.122202442352]

        self.box_coord = [0.29370, 0.16464]
        self.box_orient = [2.220, -2.197, -0.009]

    def _initial_position(self):
        orientation = orientation_position(None, None)[0]
        self.gm.move_robot(self.original_pose_coord, orientation, 'up', self.original_joint, wait_time=2, velocity=0.2)

    def move_piece(self, movement):
        self._initial_position()

        # Extract position and orientations
        position = self.bp.decode_move(movement)
        q_init, q_final, orientation_init, orientation_final = self.posManager.qs_orient_position(movement)
        orientation_init, orientation_final = self.posManager.winning_orientation_position(movement)

        # Move to first position of the movement: up, down, take chess piece, up
        self.gm.move_robot([position[0], position[1]], orientation_init, 'up', q_init)
        self.gm.open_gripper()
        self.gm.move_robot([position[0], position[1]], orientation_init, 'down', q_init, wait_time=2.5)

        # Take piece
        self.gm.close_gripper()
        self.gm.move_robot([position[0], position[1]], orientation_init, 'up', q_init)

        # Move to second position of the movement: up, down, leave chess piece, up
        self.gm.move_robot([position[2], position[3]], orientation_final, 'up', q_final)
        self.gm.move_robot([position[2], position[3]], orientation_final, 'down', q_final, wait_time=2.5)
        
        # Leave piece
        self.gm.open_gripper()
        self.gm.move_robot([position[2], position[3]], orientation_final, 'up', q_final)
        self.gm.close_gripper()

    def capture_piece(self, movement):
        self._initial_position()

        # Extract position and orientations
        position = self.bp.decode_move(movement)
        q_init, q_final, orientation_init, orientation_final = self.posManager.qs_orient_position(movement)
        orientation_init, orientation_final = self.posManager.winning_orientation_position(movement)

        # Move to last position of the movement to remove the target piece: up, down, take chess piece, up
        self.gm.move_robot([position[2], position[3]], orientation_final, 'up', q_final)
        self.gm.open_gripper()
        self.gm.move_robot([position[2], position[3]], orientation_final, 'down', q_final, wait_time=2)

        # Take piece
        self.gm.close_gripper()
        self.gm.move_robot([position[2], position[3]], orientation_final, 'up', q_final)          

        ############################################################################################################
        # TODO: Mode to the dummy box
        # Move to the dummy box
        self.gm.move_robot(self.box_coord, self.box_orient, 'up', wait_time=3.5)
        self.gm.open_gripper()
        ############################################################################################################
