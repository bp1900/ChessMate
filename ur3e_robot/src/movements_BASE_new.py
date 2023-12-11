# Echo client program
import socket
import time
import chess_board
import struct
import numpy as np

from gripper import send_info

# Connnect to robot
HOST = "10.10.73.239" # The remote host (robot IP)
PORT = 30002 # The same port as used by the server

# Conversion rows and columns
conversion_table_columns = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
conversion_table_rows = {'1': 0, '2': 1, '3': 2, '4': 3, '5': 4, '6': 5, '7': 6, '8': 7}


qs = np.zeros((4,4,6))
qs[3,0] = [-0.46321038, -1.1664035, -1.89926729, -1.5566592, -4.78307482, 0.22392574] # Degrees transformed to radians
# qs[3,1] = [-0.1527163, -0.93811447, -2.17363305, -1.4170328, -4.68114759, 6.1540309]
qs[3,1] = [-0.1527163, -0.93811447, -2.17363305, -1.4170328, -4.68114759, 0.52656584]
qs[3,2] = [0.57735492, -0.826937, -2.10155095, -1.78913702, -4.70174247, 0.52656584]
qs[3,3] = [0.74892078, -0.826937, -2.16961879, -1.77046199, -4.60260777, 0.77562432]

# qs[2,0] = [-0.189019162679099711, -1.7093755, -1.2716469, -1.7442821, -4.722861, 6.08177431]
# qs[2,1] = [-0.189019162679099711, -1.7093755, -1.2716469, -1.7442821, -4.722861, 6.08177431]
qs[2,0] = [-0.189019162679099711, -1.7093755, -1.2716469, -1.7442821, -4.722861, 0.3837979]
qs[2,1] = [-0.189019162679099711, -1.7093755, -1.2716469, -1.7442821, -4.722861, 0.3837979]
qs[2,2] = [0.39566614, -1.4749778, -1.5100589, -1.7442821, -4.71291258, 0.3837979]
qs[2,3] = [0.39566614, -1.4749778, -1.5100589, -1.7442821, -4.71291258, 0.3837979]

# qs[1,0] = [-0.189019162679099711, -1.7093755, -1.2716469, -1.7442821, -4.722861, 6.08177431]
# qs[1,1] = [-0.189019162679099711, -1.7093755, -1.2716469, -1.7442821, -4.722861, 6.08177431]
qs[1,0] = [-0.189019162679099711, -1.7093755, -1.2716469, -1.7442821, -4.722861, 0.3837979]
qs[1,1] = [-0.189019162679099711, -1.7093755, -1.2716469, -1.7442821, -4.722861, 0.3837979]
qs[1,2] = [0.39566614, -1.4749778, -1.5100589, -1.7442821, -4.71291258, 0.3837979]
qs[1,3] = [0.39566614, -1.4749778, -1.5100589, -1.7442821, -4.71291258, 0.3837979]

#qs[0,0] = [-0.31346113, -1.83207212, -1.5823155, -0.95207711, -4.59998978, 5.92644001]
#qs[0,1] = [-0.07766715, -1.651256, -1.80554311, -0.89483031, -4.66770855, 6.1540309]
qs[0,0] = [-0.31346113, -1.83207212, -1.5823155, -0.95207711, -4.59998978, 0.397586]
qs[0,1] = [-0.07766715, -1.651256, -1.80554311, -0.89483031, -4.66770855, 0.1286308]
qs[0,2] = [0.19757127, -1.5222762, -1.93661734, -0.89430671, -4.76492339, 0.1286308]
qs[0,3] = [0.48205994, -1.471138, -1.97222, -0.93741634, -4.8614401, 0.397586]

orients = np.zeros((4,4, 3)) # RX, RY, RZ
# orients[3,0] = [2.323, -2.313, 0.390]
orients[3,0] = [2.202, -2.246, 0.033]
orients[3,1] = [2.287, -2.334, 0.209]
orients[3,2] = [2.274, -2.161, -0.017]
# orients[3,3] = [2.147, -2.212, -0.169]
orients[3,3] = [2.161, -2.284, -0.035]

orients[2,0] = [2.220, -2.197, -0.009]
orients[2,1] = [2.220, -2.197, -0.009]
orients[2,2] = [2.220, -2.197, -0.009]
orients[2,3] = [2.220, -2.197, -0.009]

orients[1,0] = [2.220, -2.197, -0.009]
orients[1,1] = [2.220, -2.197, -0.009]
orients[1,2] = [2.220, -2.197, -0.009]
orients[1,3] = [2.220, -2.197, -0.009]

# orients[0,0] = [2.449, -2.308, 0.445]
orients[0,0] = [2.337, -2.248, 0.171]
orients[0,1] = [2.449, -2.308, 0.445]
orients[0,2] = [2.449, -2.308, 0.445]
# orients[0,3] = [2.449, -2.308, 0.445]
orients[0,3] = [2.337, -2.248, 0.171]

# Function for splitting string into individual list elements (ie: 0153 -> ['0','1','5','3'])
def split(word):
    return [char for char in word]

def split_coord(word):
    str_list = [char for char in word]
    
    final_movement = []
    for element in str_list:
        if element.isalpha():
            element = conversion_table_columns[element]
        else:
            element = conversion_table_rows[element]
        final_movement.append(int(element))

    return final_movement

def decode_movement(movement, cb):
    str_list = split(movement)
    str_list = str_list[:-1]

    print(f'Str list: {str_list}')
    final_movement = []

    for element in str_list:
        if element.isalpha():
            element = conversion_table_columns[element]
        else:
            element = conversion_table_rows[element]
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

def qs_orient_position(movement):

    col_init, row_init, col_final, row_final = split_coord(movement)

    print(col_init, row_init, col_final, row_final)

    quadrant_init = [row_init // 2, col_init // 2]
    quadrant_final = [row_final // 2, col_final // 2]

    print(quadrant_init)
    print(quadrant_final)

    q_init = qs[quadrant_init[0], quadrant_init[1]]
    q_final = qs[quadrant_final[0], quadrant_final[1]]

    orient_init = orients[quadrant_init[0], quadrant_init[1]]
    orient_final = orients[quadrant_final[0], quadrant_final[1]]

    print(q_init, q_final, orient_init, orient_final)

    return list(q_init), list(q_final), list(orient_init), list(orient_final)


def orientation_position(row_init, row_final):

    if row_init in {'1', '2'} and row_final in {'3', '4', '5', '6'}:
        row_final = row_init
    
    if row_final in {'1', '2'} and row_init in {'3', '4', '5', '6'}:
        row_init = row_final

    if row_init in {'7', '8'} and row_final in {'3', '4', '5', '6'}:
        row_final = row_init
    
    if row_final in {'7', '8'} and row_init in {'3', '4', '5', '6'}:
        row_init = row_final

    orientations = []
    for row in [row_init, row_final]:

        if row == '1' or row == '2':
            orientation = [2.326, -2.314, 0.407]

        elif row == '7' or row == '8':
            orientation = [2.115, -1.977, -0.481]

        else:
            orientation = [2.220321396090, -2.197400976034, -0.008928417774]

        orientations.append(orientation)

    return orientations

def winning_orientation_position(movement):
    col_init, row_init, col_final, row_final = split_coord(movement)
    print(col_init, row_init, col_final, row_final)

    quadrant_init = [row_init // 2, col_init // 2]
    quadrant_final = [row_final // 2, col_final // 2]

    print(quadrant_init)
    print(quadrant_final)

    if (quadrant_init[0] == 0 or quadrant_init[0] == 3) and (quadrant_final[0] > 0 and quadrant_final[0] < 3):
        quadrant_final[0] = quadrant_init[0]
        quadrant_final[1] = quadrant_init[1]

    elif (quadrant_init[0] > 0 and quadrant_init[0] < 3) and (quadrant_final[0] == 0 or quadrant_final[0] == 3):
        quadrant_init[0] = quadrant_final[0]
        quadrant_init[1] = quadrant_final[1]

    orient_init = orients[quadrant_init[0], quadrant_init[1]]
    orient_final = orients[quadrant_final[0], quadrant_final[1]]

    print(f'Orirnt_ini: {orient_init}')
    print(f'Orient_fi: {orient_final}')

    print(f'Winning orientation: {quadrant_init[0]}, {quadrant_init[1]}, {quadrant_final[0]}, {quadrant_final[1]} ')
    return orient_init, orient_final


# Variables
original_joint = [0.0401425728, -1.5613715488, -1.4295991903, -1.7366026057, -4.7193702974, 0.028099801]
original_pose_coord  = [0.293694398621, -0.122202442352]                        # [0.293694398621, -0.122202442352, 0.105926875934]
original_pose_orient_1 = [2.326, -2.314, 0.407]       # [2.220321396090, -2.197400976034, -0.008928417774]
original_pose_orient_8 = [2.115, -1.977, -0.481]

box_coord = [0.29370, 0.16464] #[0.30932, -0.35365]
box_orient = [2.220, -2.197, -0.009] #[1.904, -2.124, 0.200]

def main():

    # Create connection
    print("Start...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    print("Connected...")

    #TODO: Remove and change for a gripper movement
    fixed_z_up = 0.105926875934
    fixed_z_down = .0353469060551
    orientation = [2.220321396090, -2.197400976034, -0.008928417774]  # (roll, pitch, yaw)
    # cb = chess_board.chess_board(x0=0.4187, y0=-0.24738, x7=0.15521, y7=0.01008)  # Chess borders
    # cb = chess_board.chess_board(x0=0.43646, y0=-0.25540, x7=0.15070, y7=0.02702)
    cb = chess_board.chess_board(x0=0.43646, y0=-0.2545, x7=0.15070, y7=0.02702)

    # Information of the tool
    command = f"set_tcp(p[0.0,0.0,0.2286,0.0,0.0,0.0])\n"
    s.send(command.encode())

    # Main loop for chess program
    while (True):

        # Orientation of the TCP
        orientation = orientation_position(None, None)[0]

        # Move to the original position
        # command = f"movej(get_inverse_kin(p[.293694398621, -.122202442352, .105926875934, 2.220321396090, -2.197400976034, -.008928417774], [0.0401425728, -1.5613715488, -1.4295991903, -1.7366026057, -4.7193702974, 0.028099801]), a=1., v=0.2)\n"
        command = f"movej(get_inverse_kin(p[{original_pose_coord[0]}, {original_pose_coord[1]}, {fixed_z_up}, {orientation[0]}, {orientation[1]}, {orientation[2]}], {original_joint}), a=1., v=0.2, t=3)\n"
        s.send(command.encode())
        time.sleep(2)

        # Movement: obtain positions
        movement = input("Enter the movement in the following format (e.g. a1b20)") # --> Last value means: 0 = not killing // 1 = killing 
        print('State your move')

        position = decode_movement(movement, cb)
        print(f'Movement: {position}')

        ############################################################################################################

        if movement[-1] == '0': # Not killing

            # orientation_init, orientation_final = orientation_position(movement[1], movement[3])
            # q_init, q_final = qs_position(movement[:-1])
            q_init, q_final, orientation_init, orientation_final = qs_orient_position(movement[:-1])
            orientation_init, orientation_final = winning_orientation_position(movement[:-1])

            # Move to first position of the movement: up, down, take chess piece, up
            command = f"movej(get_inverse_kin(p[{position[1]}, {position[2]}, {fixed_z_up}, {orientation_init[0]}, {orientation_init[1]}, {orientation_init[2]}], {q_init}, maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=3)\n"
            print(command)
            s.send(command.encode())
            time.sleep(3.5)

            s = open_gripper(s)

            command = f"movej(get_inverse_kin(p[{position[1]}, {position[2]}, {fixed_z_down}, {orientation_init[0]}, {orientation_init[1]}, {orientation_init[2]}], {q_init}, maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=2)\n"
            s.send(command.encode())
            time.sleep(2.5)

            # Take piece
            s = close_gripper(s)

            command = f"movej(get_inverse_kin(p[{position[1]}, {position[2]}, {fixed_z_up}, {orientation_init[0]}, {orientation_init[1]}, {orientation_init[2]}], {q_init}, maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=3)\n"
            s.send(command.encode())
            time.sleep(3.5)

            ############################################################################################################

            # Move to second position of the movement: up, down, leave chess piece, up
            command = f"movej(get_inverse_kin(p[{position[3]}, {position[4]}, {fixed_z_up}, {orientation_final[0]}, {orientation_final[1]}, {orientation_final[2]}], {q_final}, maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=3)\n"
            s.send(command.encode())
            time.sleep(3.5)

            command = f"movej(get_inverse_kin(p[{position[3]}, {position[4]}, {fixed_z_down}, {orientation_final[0]}, {orientation_final[1]}, {orientation_final[2]}], {q_final}, maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=2)\n"
            s.send(command.encode())
            time.sleep(2.5)

            # Leave piece
            s = open_gripper(s)

            command = f"movej(get_inverse_kin(p[{position[3]}, {position[4]}, {fixed_z_up}, {orientation_final[0]}, {orientation_final[1]}, {orientation_final[2]}], {q_final}, maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=3)\n"
            s.send(command.encode())
            time.sleep(3.5)

            s = close_gripper(s)

        else: # killing 

            q_init, q_final, orientation_init, orientation_final = qs_orient_position(movement[:-1])
            orientation_init, orientation_final = winning_orientation_position(movement[:-1])

            # Move to last position of the movement to remove the target piece: up, down, take chess piece, up
            command = f"movej(get_inverse_kin(p[{position[3]}, {position[4]}, {fixed_z_up}, {orientation_final[0]}, {orientation_final[1]}, {orientation_final[2]}], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=3)\n"
            s.send(command.encode())
            time.sleep(3.5)

            s = open_gripper(s)

            command = f"movej(get_inverse_kin(p[{position[3]}, {position[4]}, {fixed_z_down}, {orientation_final[0]}, {orientation_final[1]}, {orientation_final[2]}], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=2)\n"
            s.send(command.encode())
            time.sleep(2.5)

            # Take piece
            s = close_gripper(s)
            
            command = f"movej(get_inverse_kin(p[{position[3]}, {position[4]}, {fixed_z_up}, {orientation_final[0]}, {orientation_final[1]}, {orientation_final[2]}], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=3)\n"
            s.send(command.encode())
            time.sleep(3.5)

            ############################################################################################################
            # TODO: Mode to the dummy box
            # Move to the dummy box
            command = f"movej(get_inverse_kin(p[{box_coord[0]}, {box_coord[1]}, {fixed_z_up}, {box_orient[0]}, {box_orient[1]}, {box_orient[2]}], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=3)\n"
            s.send(command.encode())
            time.sleep(3.5)

            # Open gripper
            s = open_gripper(s)

            ############################################################################################################

            # Move to first position of the movement: up, down, leave chess piece, up
            command = f"movej(get_inverse_kin(p[{position[1]}, {position[2]}, {fixed_z_up}, {orientation_init[0]}, {orientation_init[1]}, {orientation_init[2]}], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=3)\n"
            s.send(command.encode())
            time.sleep(3.5)

             # Pick piece
            s = open_gripper(s)

            command = f"movej(get_inverse_kin(p[{position[1]}, {position[2]}, {fixed_z_down}, {orientation_init[0]}, {orientation_init[1]}, {orientation_init[2]}], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=2)\n"
            s.send(command.encode())
            time.sleep(2.5)

            s = close_gripper(s)


            command = f"movej(get_inverse_kin(p[{position[1]}, {position[2]}, {fixed_z_up}, {orientation_init[0]}, {orientation_init[1]}, {orientation_init[2]}], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=3)\n"
            s.send(command.encode())
            time.sleep(3.5)

            ############################################################################################################

            # Move to second position of the movement: up, down, leave chess piece, up
            command = f"movej(get_inverse_kin(p[{position[3]}, {position[4]}, {fixed_z_up}, {orientation_final[0]}, {orientation_final[1]}, {orientation_final[2]}], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=3)\n"
            s.send(command.encode())
            time.sleep(3.5)

            command = f"movej(get_inverse_kin(p[{position[3]}, {position[4]}, {fixed_z_down}, {orientation_final[0]}, {orientation_final[1]}, {orientation_final[2]}], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=2)\n"
            s.send(command.encode())
            time.sleep(2.5)

            # Leave piece
            s = open_gripper(s)

            command = f"movej(get_inverse_kin(p[{position[3]}, {position[4]}, {fixed_z_up}, {orientation_final[0]}, {orientation_final[1]}, {orientation_final[2]}], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=3)\n"
            s.send(command.encode())
            time.sleep(3.5)

            s = close_gripper(s)




if __name__ == "__main__":
    main()
