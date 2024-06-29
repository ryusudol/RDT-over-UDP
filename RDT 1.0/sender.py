import socket
import sys
from PASender import PASender
from logHandler import logHandler


if __name__ == "__main__":
    try:
        dst_addr = sys.argv[1]  # receiver IP address
        window_size = int(sys.argv[2])  # window size
        src_filename = sys.argv[3]  # sending file name
        log_filename = sys.argv[4]  # log file name
    except IndexError:
        print("How To Use")
        print(
            "python sender.py <receiver's IP address> <window size> <source file name> <log file name>"
        )
        sys.exit(1)

    logger = logHandler()
    logger.startLogging(log_filename)

    PORT = 10090
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("localhost", PORT))  # localhost -> VM ip: 192.168.64.17
    sender = PASender(sock, config_file="config.txt")
    with open(src_filename, "rb") as file:
        file_content = file.read()

    chunks = [file_content[i : i + 1024] for i in range(0, len(file_content), 1024)]
    for chunk in chunks:
        sender.sendto_bytes(chunk, (dst_addr, PORT))
        logger.writePkt(0, logHandler.SEND_DATA)

    logger.writeEnd()
    sock.close()
