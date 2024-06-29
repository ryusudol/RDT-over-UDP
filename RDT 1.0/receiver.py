import sys
import socket

if __name__ == "__main__":
    try:
        res_filename = sys.argv[1]  # res file name
        log_filname = sys.argv[2]  # log file name
    except IndexError:
        print("How To Use")
        print("python receiver.py <result file name> <log file name>")
        sys.exit(1)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    PORT = 10090
    sock.bind(("localhost", PORT))  # localhost -> VM ip: 192.168.64.21

    packet_data = sock.recv(2048)
    with open(log_filname, "wb") as file:
        file.write(packet_data)

    sock.close()
