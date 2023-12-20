import socket
import time


class GripperManager:
    def __init__(self, host='10.10.73.237', port=30002, sleep_time=2, test_mode=False):
        self.host = host  # The remote host (robot IP)
        self.port = port  # The same port as used by the server
        self.sleep_time = sleep_time
        self.test_mode = test_mode

        self.fixed_z_up = 0.12 # 0.105926875934
        self.fixed_z_down_take  = .0353469060551
        self.fixed_z_down_leave = .037
        self.fixed_z_down_take_pawn  = .032
        self.fixed_z_down_leave_pawn  = .0332
        self.fixed_z_kill = .06

        if not self.test_mode:
            print('Connecting to arm...')
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((host, port))
            print('Connected to arm')
        else:
            print("Test mode enabled - No actual connection to arm")

    def reconnect(self):
        if not self.test_mode:
            self.s.close()
            # time.sleep(1)
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((self.host, self.port))

    def open_gripper(self):
        if not self.test_mode:
            self.reconnect()
            send_info(1, self.host, self.port)
            print("Gripper opened (test mode)") if self.test_mode else None
            time.sleep(self.sleep_time)

    def close_gripper(self):
        if not self.test_mode:
            self.reconnect()
            send_info(0, self.host, self.port)
            print("Gripper closed (test mode)") if self.test_mode else None
            time.sleep(self.sleep_time)

    def send_command(self, command):
        if not self.test_mode:
            self.s.send(command.encode())
        else:
            print(f"Command sent (test mode): {command}")

    def move_robot(self, position, orientation, fixed_z_height, q_vals=None, wait_time=2.5, velocity=0.2, checkmate=False):
        if q_vals is None:
            q_vals = ""
        else:
            q_vals = str(q_vals) + ','

        if fixed_z_height == 'up':
            fixed_z_height = self.fixed_z_up
        elif fixed_z_height == 'down_take':
            fixed_z_height = self.fixed_z_down_take
        elif fixed_z_height == 'down_leave':
            fixed_z_height = self.fixed_z_down_leave
        elif fixed_z_height == 'down_take_pawn':
            fixed_z_height = self.fixed_z_down_take_pawn
        elif fixed_z_height == 'down_leave_pawn':
            fixed_z_height = self.fixed_z_down_leave_pawn

        if checkmate:
            fixed_z_height = self.fixed_z_kill

        command = f"movej(get_inverse_kin(p[{position[0]}, {position[1]}, {fixed_z_height}, {orientation[0]}, {orientation[1]}, {orientation[2]}], {q_vals} maxPositionError=1e-1, maxOrientationError=1e-3), a=0.02, v={velocity}, t={wait_time})\n"
        # command = f"movej(get_inverse_kin(p[{position[0]}, {position[1]}, {fixed_z_height}, {orientation[0]}, {orientation[1]}, {orientation[2]}], {q_vals} maxPositionError=1e-1, maxOrientationError=1e-3), a=0.1, v={velocity})\n"
        self.send_command(command)
        # time.sleep(self.sleep_time)
        if not self.test_mode:
            time.sleep(wait_time+0.2)

# POSSIBLEMENT POSAR AIXO DINS LA CLASSE?
def send_info(v, HOST, PORT):
    # gripper = rpc_factor("xmlrpc", "http://"+HOST+":41414")

    # def grasp():
    #     gripper.rg_grip(index, width_closed, closure_force)


    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    # s.sendall(b'GET POS\n')
    # data = s.recv(1024)
    #print('holaa')

    # print(data)

    if v == 0:
        f = open(r"src\robot\src\\gripper_CIR_close.script", "rb")
    else:
        f = open(r"src\robot\src\gripper_CIR_open.script", "rb")
    # l = f.read(2048)
    # print(l)

    # f = open("commands.txt", "rb")
    # # l = f.read(1024)
    l = f.readlines()
    # # print(l)

    # while (l):
    for line in l:
        #print(line)
        s.send(line)
        # l = f.read(1024)
        # time.sleep(5)

    f.close()
    s.close()

