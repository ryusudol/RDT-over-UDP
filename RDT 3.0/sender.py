import socket
import sys
from PASender import PASender
from logHandler import logHandler


def calculate_checksum(data):
    if len(data) % 2:
        data += b"\0"

    checksum_value = 0
    for i in range(0, len(data), 2):
        current_word = (data[i] << 8) | data[i + 1]
        checksum_value += current_word
        checksum_value = (checksum_value & 0xFFFF) + (checksum_value >> 16)

    checksum_value = ~checksum_value & 0xFFFF
    return checksum_value


if __name__ == "__main__":
    try:
        dst_addr = sys.argv[1]  # receiver IP address
        window_size = int(sys.argv[2])  # window size
        src_filename = sys.argv[3]  # sending file name
        log_filename = sys.argv[4]  # log file name
    except IndexError:
        print("How To Use")
        print(
            "python sender py <receiver's IP address> <window size> <source file name> <log file name>"
        )
        sys.exit(1)

    logger = logHandler()
    logger.startLogging(log_filename)

    PORT = 10090
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("192.168.64.17", PORT))

    sender = PASender(sock, config_file="./config.txt")
    with open(src_filename, "rb") as file:
        file_content = file.read()

    seq_num = 0
    chunks = [file_content[i : i + 1024] for i in range(0, len(file_content), 1024)]
    for chunk in chunks:
        checksum = calculate_checksum(chunk)
        packet = seq_num.to_bytes(1, "big") + checksum.to_bytes(2, "big") + chunk
        sender.sendto_bytes(packet, (dst_addr, PORT))
        logger.writePkt(seq_num, logger.SEND_DATA)

        while True:
            try:
                sock.settimeout(0.01)
                ack_packet, _ = sock.recvfrom(4)
                received_ack_num = ack_packet[0]

                if received_ack_num == seq_num:
                    logger.writePkt(seq_num, logger.SUCCESS_ACK)
                    seq_num = 1 - seq_num
                    break
                else:
                    logger.writeAck(received_ack_num, logger.WRONG_SEQ_NUM)
            except socket.timeout:
                logger.writeTimeout(seq_num)
                sender.sendto_bytes(packet, (dst_addr, PORT))
                logger.writePkt(seq_num, logger.SEND_DATA_AGAIN)

    end_packet = b"END"
    sender.sendto_bytes(end_packet, (dst_addr, PORT))
    sock.settimeout(None)
    sock.recvfrom(1)

    logger.writeEnd()
    sock.close()
