import socket
import time


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
