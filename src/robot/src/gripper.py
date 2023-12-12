import socket
import time


class GripperManager:
    def __init__(self, host='10.10.73.239', port=30002, sleep_time=2, test_mode=False):
        self.host = host  # The remote host (robot IP)
        self.port = port  # The same port as used by the server
        self.sleep_time = sleep_time
        self.test_mode = test_mode

        self.fixed_z_up = 0.105926875934
        self.fixed_z_down = .0353469060551

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
            time.sleep(1)
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((self.host, self.port))

    def open_gripper(self):
        self.reconnect()
        if not self.test_mode:
            send_info(1)
        print("Gripper opened (test mode)") if self.test_mode else None
        time.sleep(self.sleep_time)

    def close_gripper(self):
        self.reconnect()
        if not self.test_mode:
            send_info(0)
        print("Gripper closed (test mode)") if self.test_mode else None
        time.sleep(self.sleep_time)

    def send_command(self, command):
        if not self.test_mode:
            self.s.send(command.encode())
        else:
            print(f"Command sent (test mode): {command}")

    def move_robot(self, position, orientation, fixed_z_height, q_vals=None, wait_time=3.5, velocity=0.1):
        if q_vals is None:
            q_vals = "[...]"

        if fixed_z_height == 'up':
            fixed_z_height = self.fixed_z_up
        else:
            fixed_z_height = self.fixed_z_down

        command = f"movej(get_inverse_kin(p[{position[0]}, {position[1]}, {fixed_z_height}, {orientation[0]}, {orientation[1]}, {orientation[2]}], {q_vals}, maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v={velocity}, t={wait_time})\n"
        self.send_command(command)
        time.sleep(self.sleep_time)

'''
class GripperManager:
    def __init__(self, host='10.10.73.239', port=30002, sleep_time=2):
        self.host = host # The remote host (robot IP)
        self.port = port # The same port as used by the server
        self.sleep_time = sleep_time

        self.fixed_z_up = 0.105926875934
        self.fixed_z_down = .0353469060551

        print('Connecting to arm...')
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((host, port))
        print('Connected to arm')

    def reconnect(self):
        self.s.close()
        time.sleep(1)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.host, self.port))

    def open_gripper(self):
        # Open gripper
        self.reconnect()
        send_info(1)
        time.sleep(self.sleep_time)

    def close_gripper(self):
        # Close gripper
        self.reconnect()
        send_info(0)
        time.sleep(self.sleep_time)

    def send_command(self, command):
        self.s.send(command.encode()) 

    def move_robot(self, position, orientation, fixed_z_height, q_vals=None, wait_time=3.5, velocity=0.1):
        if q_vals is None:
            q_vals = "[...]"

        if fixed_z_height == 'up':
            fixed_z_height = self.fixed_z_up
        else:
            fixed_z_height = self.fixed_z_down

        command = f"movej(get_inverse_kin(p[{position[0]}, {position[1]}, {fixed_z_height}, {orientation[0]}, {orientation[1]}, {orientation[2]}], {q_vals}, maxPositionError=1e-1, maxOrientationError=1e-3), a=1.0, v={velocity}, t={wait_time})\n"
        self.send_command(command)
        time.sleep(self.sleep_time)
'''


# POSSIBLEMENT POSAR AIXO DINS LA CLASSE?
def send_info(v):
    HOST = "10.10.73.239" # The remote host (robot IP)
    PORT = 30002 # The same port as used by the server

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
        f = open("gripper_CIR_close.script", "rb")
    else:
        f = open("gripper_CIR_open.script", "rb")
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

def main():
    send_info()


if __name__ == "__main__":
    main()
