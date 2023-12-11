# Echo client program
import socket
import time
import chess_board
import struct


from gripper import send_info

HOST = "10.10.73.239" # The remote host (robot IP)
PORT = 30002 # The same port as used by the server

conversion_table_rows = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
conversion_table_columns = {'1': 0, '2': 1, '3': 2, '4': 3, '5': 4, '6': 5, '7': 6, '8': 7}

# Function for splitting string into individual list elements (ie: 0153 -> ['0','1','5','3'])
def split(word):
    return [char for char in word]

def decode_movement(movement, cb):
    str_list = split(movement)
    print(f'Str list: {str_list}')
    final_movement = []

    for element in str_list:
        if element.isalpha():
            element = conversion_table_rows[element]
        else:
            element = conversion_table_columns[element]
        final_movement.append(int(element))

    print(f'Final movement: {final_movement}')

    x = cb.move(final_movement[0], final_movement[1], final_movement[2], final_movement[3])
    x = x[1:-1].split(',')
    vals = []
    for val in x:
        vals.append(float(val))

    return vals


def main():

    # Create connection
    print("Start...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    print("Connected...")

    #
    # # Initial values
    # InitialPosition_p=[0.281101042253, -0.105027015980, 0.303847033251, 2.238860342959, -2.203064438959, -0.000119867082]
    # InitialPosition_q=[0.09497137367725372, -1.4522820276072999, -1.681410789489746, -1.5775052509703578, -4.711585823689596, 0.07784082740545273]
    #
    # # Set the robot to the initial position
    # command = f'movej(get_inverse_kin(p={InitialPosition_p}, qnear={InitialPosition_q}), a=1.3962634015954636, v=1.0471975511965976)\n'
    # s.send(command.encode())

    #TODO: Remove and change for a gripper movement
    fixed_z_up = .105926875934
    fixed_z_down = .08
    orientation = [2.220321396090, -2.197400976034, -.008928417774]  # (roll, pitch, yaw)
    cb = chess_board.chess_board(x0=0.4187, y0=-0.24738, x7=0.15521, y7=0.01008)  # Chess borders

    command = f"set_tcp(p[0.0,0.0,0.2286,0.0,0.0,0.0])\n"
    s.send(command.encode())

    # Main loop for chess program
    i = 0
    while (True):
        i += 1
        # TODO: Move to the original position
        # command = f"movej(p[.293694398621, -.122202442352, .105926875934, 2.220321396090, -2.197400976034, -.008928417774], a=1., v=0.2)\n"
        command = f"movej(get_inverse_kin(p[.293694398621, -.122202442352, .105926875934, 2.220321396090, -2.197400976034, -.008928417774], [0.0401425728, -1.5613715488, -1.4295991903, -1.7366026057, -4.7193702974, 0.028099801]), a=1., v=0.2)\n"
        # command = f"movej([0.0401425728, -1.5613715488, -1.4295991903, -1.7366026057, -4.7193702974, 0.028099801]), a=1., v=0.2)\n"
        s.send(command.encode())
        time.sleep(2)

        movement = input("Enter the movement in the following format (e.g. a1b2)")
        print('State your move')

        position = decode_movement(movement, cb)
        print(f'Movement: {position}')
        print(f"all: {[{position[1]}, {position[2]}, {fixed_z_up}, {orientation[0]}, {orientation[1]}, {orientation[2]}]}")

        # TODO: Move to the origin position
        # command = f"movel([-0.25863677660097295, -2.6882792911925257, 0.2412784735309046, -2.2638584576048792, -4.711334292088644, -0.2799947897540491], a=0.5, v=0.1)\n"
        # s.send(command.encode())
        # time.sleep(3)

        print("Second move")

        # f = open("gripper_CIR.script", "rb")
        # l = f.readlines()
        # for line in l:
        #     print(line)
        #     s.send(line)
        
        # f.close()
        # s.close()

        command = f"movej(get_inverse_kin(p[.418768537430, -.247381723333, .103469060551, 2.239032681645, -2.203063869620, .000131692615], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=3)\n"
        # command = f"movej(get_inverse_kin(p[.418768537430, -.247381723333, .303469060551, 2.239032681645, -2.203063869620, .000131692615], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1)\n"
        s.send(command.encode())
        time.sleep(5)

        command = f"movej(get_inverse_kin(p[.418768537430, -.247381723333, .0303469060551, 2.239032681645, -2.203063869620, .000131692615], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=3)\n"
        s.send(command.encode())
        time.sleep(5)

        s.close()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        send_info(1)
        time.sleep(2)

        s.close()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        send_info(0)
        time.sleep(2)

        command = f"movej(get_inverse_kin(p[.418768537430, -.247381723333, .103469060551, 2.239032681645, -2.203063869620, .000131692615], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1, t=3)\n"
        # command = f"movej(get_inverse_kin(p[.418768537430, -.247381723333, .303469060551, 2.239032681645, -2.203063869620, .000131692615], maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v=0.1)\n"
        s.send(command.encode())
        time.sleep(5)

        print("new")
        


        """
        # TODO: Move to the origin position
        command = f"movel([0.40489742159843445, -2.0024625263609828, -1.034292459487915, -1.6744262180724085, -4.711186114941732, 0.3861035406589508], a=0.5, v=0.1)\n"
        # s.send(command.encode())
        # time.sleep(3)

        print("Second move")

        # TODO: Move to the origin position
        command = f"movel([-0.5770018736468714, -1.3882551503232499, -1.7345777750015259, -1.5880433521666468, -4.711750570927755, -0.594126049672262], a=0.5, v=0.1)\n"
        # s.send(command.encode())
        # time.sleep(3)

        print("Second move")


        # TODO: Move to the origin position
        command = f"movel([0.9436919689178467, -0.6639978450587769, -2.1697356700897217, -1.8485046825804652, -4.590174976979391, -0.30857783952821904], a=0.5, v=0.1)\n"
        # s.send(command.encode())
        # time.sleep(3)

        print("Second move")

        # TODO: Close the wrapper
        command = f"set_configurable_digital_out(0,True)\n"
        # s.send(command.encode())
        time.sleep(2)

        # TODO: Open the wrapper
        command = f"rg_grip(50.0, 40.0, 1)\n"
        s.send(command.encode())
        time.sleep(2)

        # TODO: Close the wrapper
        command = f"rg_grip(rg_Width+5, 40, rg_index_get())\n" # rg_payload_set(0.0, l_index = 0, use_guard = True)\n"
        s.send(command.encode())
        time.sleep(2)

        # TODO: Decrease z axis
        command = f"movel(p[{position[1]}, {position[2]}, {fixed_z_down}, {orientation[0]}, {orientation[1]}, {orientation[2]}], a=1.0, v=0.1)\n"
        s.send(command.encode())
        time.sleep(2)

        # TODO: Close the wrapper
        command = f"set_configurable_digital_out(0,False)\n"
        # s.send(command.encode())
        time.sleep(2)

        # TODO: Increase z axis
        command = f"movel(p[{position[1]}, {position[2]}, {fixed_z_up}, {orientation[0]}, {orientation[1]}, {orientation[2]}], a=1.0, v=0.1)\n"
        # s.send(command.encode())
        time.sleep(2)

        # TODO: Move to Destination
        command = f"movel(p[{position[3]}, {position[4]}, {fixed_z_up}, {orientation[0]}, {orientation[1]}, {orientation[2]}], a=1.0, v=0.1)\n"
        # s.send(command.encode())
        time.sleep(2)

        # TODO: Decrease z axis
        command = f"movel(p[{position[3]}, {position[4]}, {fixed_z_down}, {orientation[0]}, {orientation[1]}, {orientation[2]}], a=1.0, v=0.1)\n"
        # s.send(command.encode())
        time.sleep(2)

        # TODO: Open the wrapper
        command = f"set_configurable_digital_out(0,True)\n"
        # s.send(command.encode())
        time.sleep(2)

        # TODO: Increase z axis
        command = f"movel(p[{position[3]}, {position[4]}, {fixed_z_up}, {orientation[0]}, {orientation[1]}, {orientation[2]}], a=1.0, v=0.1)\n"
        # s.send(command.encode())
        time.sleep(2)
        """

    #data = s.recv(1024)
    #print(data)
    # s.close()


if __name__ == "__main__":
    main()








#
# s.send("set_digital_out(3,False)".encode() + "\n".encode())
# #s.send("set_configurable_digital_out(0,True)".encode() + "\n".encode())
# time.sleep(2)
# s.send("set_digital_out(3,True)".encode() + "\n".encode())
# time.sleep(2)
# s.send("set_digital_out(3,False)".encode() + "\n".encode())
# #s.send("set_configurable_digital_out(0,True)".encode() + "\n".encode())
# time.sleep(2)
# s.send("set_digital_out(3,True)".encode() + "\n".encode())
# time.sleep(2)
# s.send("set_digital_out(3,False)".encode() + "\n".encode())
# #s.send("set_configurable_digital_out(0,True)".encode() + "\n".encode())
# time.sleep(2)
# s.send("set_digital_out(3,True)".encode() + "\n".encode())
# time.sleep(2)
# s.send("set_digital_out(3,False)".encode() + "\n".encode())
# #s.send("set_configurable_digital_out(0,True)".encode() + "\n".encode())
# time.sleep(2)
# s.send("set_digital_out(3,True)".encode() + "\n".encode())
# time.sleep(2)
#
#
#
# #s.send("set_tool_digital_out(0,True)".encode() + "\n".encode())
# #s.send ("movej([-1.95, -1.58, 1.16, -1.15, -1.55, 1.18], a=1.0, v=0.1)".encode() + "\n".encode())
# s.send ("movej([0, -0.38, -0.02, 0, 0, 0], a=1.0, v=0.1)".encode() + "\n".encode())
# #s.send ("movej([-1.57,-1.75,-1.29,4.74,-1.74,-2.44], a=0.4, v=1.05, t=0, r=0)".encode() + "\n".encode())
# #s.send ("movel([-0.01,-0.04,0.02,4.49,1.5,4.53], a=0.04, v=1.05, t=0, r=0)".encode() + "\n".encode())
# time.sleep(2)
# data = s.recv(1024)
# print(data)
# s.close()