import chess_board
from MovementManager import MovementManager, decode_movement, orientation_position
from gripper import GripperManager

original_joint = [0.0401425728, -1.5613715488, -1.4295991903, -1.7366026057, -4.7193702974, 0.028099801]
original_pose_coord  = [0.293694398621, -0.122202442352]                        # [0.293694398621, -0.122202442352, 0.105926875934]

box_coord = [0.29370, 0.16464]
box_orient = [2.220, -2.197, -0.009]

def main():
    # Create connection
    gm = GripperManager()

    cb = chess_board.chess_board(x0=0.43646, y0=-0.2545, x7=0.15070, y7=0.02702)

    # Information of the tool
    gm.send_command(f"set_tcp(p[0.0,0.0,0.2286,0.0,0.0,0.0])\n")

    # Main loop for chess program
    while (True):
        orientation = orientation_position(None, None)[0]

        # Move to the original position
        #command = f"movej(get_inverse_kin(p[{original_pose_coord[0]}, {original_pose_coord[1]}, {'up'}, {orientation[0]}, {orientation[1]}, {orientation[2]}], {original_joint}), a=1., v=0.2, t=3)\n"
        gm.move_robot(original_pose_coord, orientation, 'up', original_joint, wait_time=2)

        # Movement: obtain positions
        movement = input("Enter the movement in the following format (e.g. a1b20)") # --> Last value means: 0 = not killing // 1 = killing 
        print('State your move')

        position = decode_movement(movement, cb)
        print(f'Movement: {position}')
        posManager = MovementManager()

        ############################################################################################################

        if movement[-1] == '0': # Not killing
            q_init, q_final, orientation_init, orientation_final = posManager.qs_orient_position(movement[:-1])
            orientation_init, orientation_final = posManager.winning_orientation_position(movement[:-1])

            # Move to first position of the movement: up, down, take chess piece, up
            gm.move_robot([position[1], position[2]], orientation_init, 'up', q_init)
            gm.open_gripper()
            gm.move_robot([position[1], position[2]], orientation_init, 'down', q_init, wait_time=2.5)

            # Take piece
            gm.close_gripper()
            gm.move_robot([position[1], position[2]], orientation_init, 'up', q_init)
            ############################################################################################################

            # Move to second position of the movement: up, down, leave chess piece, up
            gm.move_robot([position[3], position[4]], orientation_final, 'up', q_final)
            gm.move_robot([position[3], position[4]], orientation_final, 'down', q_final, wait_time=2.5)
            
            # Leave piece
            gm.open_gripper()
            gm.move_robot([position[3], position[4]], orientation_final, 'up', q_final)
            gm.close_gripper()
        else: # killing 
            q_init, q_final, orientation_init, orientation_final = posManager.qs_orient_position(movement[:-1])
            orientation_init, orientation_final = posManager.winning_orientation_position(movement[:-1])

            # Move to last position of the movement to remove the target piece: up, down, take chess piece, up

            gm.move_robot([position[3], position[4]], orientation_final, 'up', q_final)
            gm.open_gripper()
            gm.move_robot([position[3], position[4]], orientation_final, 'down', q_final, wait_time=2)

            # Take piece
            gm.close_gripper()
            gm.move_robot([position[3], position[4]], orientation_final, 'up', q_final)          

            ############################################################################################################
            # TODO: Mode to the dummy box
            # Move to the dummy box
            gm.move_robot(box_coord, box_orient, 'up', wait_time=3.5)
            gm.open_gripper()
            ############################################################################################################

            # Move to first position of the movement
            #gm.move_robot([position[1], position[2]], orientation_init, 'up', q_init)
            #gm.open_gripper()
            #gm.move_robot([position[1], position[2]], orientation_init, 'down', q_init, wait_time=2.5)
            #gm.close_gripper()
            #gm.move_robot([position[1], position[2]], orientation_init, 'up', q_init)

            # Move to second position of the movement
            #gm.move_robot([position[3], position[4]], orientation_final, 'up', q_final)
            #gm.move_robot([position[3], position[4]], orientation_final, 'down', q_final, wait_time=2.5)
            #gm.open_gripper()
            #gm.move_robot([position[3], position[4]], orientation_final, 'up', q_final)
            #gm.close_gripper()

if __name__ == "__main__":
    main()
