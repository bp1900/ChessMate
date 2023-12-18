# Echo client program
import socket
import time
import chess_board
import struct

from gripper import send_info

# Connnect to robot
HOST = "10.10.73.239" # The remote host (robot IP)
PORT = 30002 # The same port as used by the server

# Conversion rows and columns
conversion_table_rows = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
conversion_table_columns = {'1': 0, '2': 1, '3': 2, '4': 3, '5': 4, '6': 5, '7': 6, '8': 7}

# Function for splitting string into individual list elements (ie: 0153 -> ['0','1','5','3'])
def split(word):
    return [char for char in word]

def decode_movement(movement, cb):
    str_list = split(movement)
    str_list = str_list[:-1]

    print(f'Str list: {str_list}')
    final_movement = []

    for element in str_list:
        if element.isalpha():
            element = conversion_table_rows[element]
        else:
            element = conversion_table_columns[element]
        final_movement.append(int(element))

    print(f'Final movement: {final_movement}')

    x = cb.move(final_movement[1], final_movement[0], final_movement[3], final_movement[2])
    x = x[1:-1].split(',')
    vals = []
    for val in x:
        vals.append(float(val))

    return vals

# Open and close gripper to manage chess pieces
def reconnect(s):

    s.close()
    time.sleep(1)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    return s

def open_gripper(s):

    # Open gripper
    s = reconnect(s)
    send_info(1)
    time.sleep(2)

    return s

def close_gripper(s):

    # Open gripper
    s = reconnect(s)
    send_info(0)
    time.sleep(2)

    return s

def orientation_position(row_init, row_final):

    orientations = []
    for row in [row_init, row_final]:

        if row == '1' or row == '2':
            orientation = [2.326, -2.314, 0.407]

        if row == '7' or row == '8':
            orientation = [2.115, -1.977, -0.481]

        else:
            orientation = [2.220321396090, -2.197400976034, -0.008928417774]

        orientations.append(orientation)

    return orientations


# Variables
original_joint = [0.0401425728, -1.5613715488, -1.4295991903, -1.7366026057, -4.7193702974, 0.028099801]
original_pose_coord  = [0.293694398621, -0.122202442352]                        # [0.293694398621, -0.122202442352, 0.105926875934]
original_pose_orient_1 = [2.326, -2.314, 0.407]       # [2.220321396090, -2.197400976034, -0.008928417774]
original_pose_orient_8 = [2.115, -1.977, -0.481]

def main():

    # Create connection
    # print("Start...")
    # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # s.connect((HOST, PORT))
    # print("Connected...")

    #TODO: Remove and change for a gripper movement
    fixed_z_up = 0.105926875934
    fixed_z_down = .0303469060551
    orientation = [2.220321396090, -2.197400976034, -0.008928417774]  # (roll, pitch, yaw)
    # cb = chess_board.chess_board(x0=0.4187, y0=-0.24738, x7=0.15521, y7=0.01008)  # Chess borders
    cb = chess_board.chess_board(x0=0.43646, y0=-0.25540, x7=0.15070, y7=0.02702)

    # Information of the tool
    # command = f"set_tcp(p[0.0,0.0,0.2286,0.0,0.0,0.0])\n"
    # s.send(command.encode())

    # Main loop for chess program
    while (True):

        # Orientation of the TCP
        orientation = orientation_position(None, None)[0]

        # Move to the original position
        # command = f"movej(get_inverse_kin(p[.293694398621, -.122202442352, .105926875934, 2.220321396090, -2.197400976034, -.008928417774], [0.0401425728, -1.5613715488, -1.4295991903, -1.7366026057, -4.7193702974, 0.028099801]), a=1., v=0.2)\n"
        command = f"movej(get_inverse_kin(p[{original_pose_coord[0]}, {original_pose_coord[1]}, {fixed_z_up}, {orientation[0]}, {orientation[1]}, {orientation[2]}], {original_joint}), a=1., v=0.2, t=3)\n"
        # s.send(command.encode())
        # time.sleep(2)

        # Movement: obtain positions
        movement = input("Enter the movement in the following format (e.g. a1b20)") # --> Last value means: 0 = not killing // 1 = killing 
        print('State your move')

        position = decode_movement(movement, cb)
        print(f'Movement: {position}')

        ############################################################################################################

        if movement[-1] == '0': # Not killing

            orientation_init, orientation_final = orientation_position(movement[1], movement[3])

            # Move to first position of the movement: up, down, take chess piece, up
            command = f"movej(get_inverse_kin(p[{position[1]}, {position[2]}, {fixed_z_up}, {orientation_init[0]}, {orientation_init[1]}, {orientation_init[2]}], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=3)\n"
            # s.send(command.encode())
            # time.sleep(3.5)

            # s = open_gripper(s)

            command = f"movej(get_inverse_kin(p[{position[1]}, {position[2]}, {fixed_z_down}, {orientation_init[0]}, {orientation_init[1]}, {orientation_init[2]}], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=2)\n"
            # s.send(command.encode())
            # time.sleep(2.5)

            # # Take piece
            # s = close_gripper(s)

            command = f"movej(get_inverse_kin(p[{position[1]}, {position[2]}, {fixed_z_up}, {orientation_init[0]}, {orientation_init[1]}, {orientation_init[2]}], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=3)\n"
            # s.send(command.encode())
            # time.sleep(3.5)

            ############################################################################################################

            # Move to second position of the movement: up, down, leave chess piece, up
            command = f"movej(get_inverse_kin(p[{position[3]}, {position[4]}, {fixed_z_up}, {orientation_final[0]}, {orientation_final[1]}, {orientation_final[2]}], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=3)\n"
            # s.send(command.encode())
            # time.sleep(3.5)

            command = f"movej(get_inverse_kin(p[{position[3]}, {position[4]}, {fixed_z_down}, {orientation_final[0]}, {orientation_final[1]}, {orientation_final[2]}], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=2)\n"
            # s.send(command.encode())
            # time.sleep(2.5)

            # Leave piece
            # s = open_gripper(s)

            command = f"movej(get_inverse_kin(p[{position[3]}, {position[4]}, {fixed_z_up}, {orientation_final[0]}, {orientation_final[1]}, {orientation_final[2]}], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=3)\n"
            # s.send(command.encode())
            # time.sleep(3.5)

            # s = close_gripper(s)

        # else: # killing 

        #     orientation_init, orientation_final = orientation_position(movement[1], movement[3])

        #     # Move to last position of the movement to remove the target piece: up, down, take chess piece, up
        #     command = f"movej(get_inverse_kin(p[{position[3]}, {position[4]}, {fixed_z_up}, {orientation_final[0]}, {orientation_final[1]}, {orientation_final[2]}], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=3)\n"
        #     s.send(command.encode())
        #     time.sleep(3.5)

        #     s = open_gripper(s)

        #     command = f"movej(get_inverse_kin(p[{position[3]}, {position[4]}, {fixed_z_down}, {orientation_final[0]}, {orientation_final[1]}, {orientation_final[2]}], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=2)\n"
        #     s.send(command.encode())
        #     time.sleep(2.5)

        #     # Take piece
        #     s = close_gripper(s)
            
        #     command = f"movej(get_inverse_kin(p[{position[3]}, {position[4]}, {fixed_z_up}, {orientation_final[0]}, {orientation_final[1]}, {orientation_final[2]}], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=3)\n"
        #     s.send(command.encode())
        #     time.sleep(3.5)

        #     ############################################################################################################
        #     # TODO: Mode to the dummy box
        #     # Move to the dummy box
        #     #command = f"movej(get_inverse_kin(p[{position[3]}, {position[4]}, {fixed_z_up}, {orientation_final[0]}, {orientation_final[1]}, {orientation_final[2]}], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=3)\n"
        #     s.send(command.encode())
        #     time.sleep(3.5)

        #     # Open gripper
        #     s = open_gripper(s)

        #     ############################################################################################################

        #     # Move to first position of the movement: up, down, leave chess piece, up
        #     command = f"movej(get_inverse_kin(p[{position[1]}, {position[2]}, {fixed_z_up}, {orientation_init[0]}, {orientation_init[1]}, {orientation_init[2]}], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=3)\n"
        #     s.send(command.encode())
        #     time.sleep(3.5)

        #      # Pick piece
        #     s = open_gripper(s)

        #     command = f"movej(get_inverse_kin(p[{position[1]}, {position[2]}, {fixed_z_down}, {orientation_init[0]}, {orientation_init[1]}, {orientation_init[2]}], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=2)\n"
        #     s.send(command.encode())
        #     time.sleep(2.5)

        #     s = close_gripper(s)


        #     command = f"movej(get_inverse_kin(p[{position[1]}, {position[2]}, {fixed_z_up}, {orientation_init[0]}, {orientation_init[1]}, {orientation_init[2]}], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=3)\n"
        #     s.send(command.encode())
        #     time.sleep(3.5)

        #     ############################################################################################################

        #     # Move to second position of the movement: up, down, leave chess piece, up
        #     command = f"movej(get_inverse_kin(p[{position[3]}, {position[4]}, {fixed_z_up}, {orientation_final[0]}, {orientation_final[1]}, {orientation_final[2]}], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=3)\n"
        #     s.send(command.encode())
        #     time.sleep(3.5)

        #     command = f"movej(get_inverse_kin(p[{position[3]}, {position[4]}, {fixed_z_down}, {orientation_final[0]}, {orientation_final[1]}, {orientation_final[2]}], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=2)\n"
        #     s.send(command.encode())
        #     time.sleep(2.5)

        #     # Leave piece
        #     s = open_gripper(s)

        #     command = f"movej(get_inverse_kin(p[{position[3]}, {position[4]}, {fixed_z_up}, {orientation_final[0]}, {orientation_final[1]}, {orientation_final[2]}], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=3)\n"
        #     s.send(command.encode())
        #     time.sleep(3.5)

        #     s = close_gripper(s)




if __name__ == "__main__":
    main()
