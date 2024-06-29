import socket
import sys
from PASender import PASender
from logHandler import logHandler


def checksum(data):
    if len(data) % 2:
        data += b"\0"

    checksum_val = 0
    for i in range(0, len(data), 2):
        current_word = (data[i] << 8) | data[i + 1]
        checksum_val += current_word
        checksum_val = (checksum_val & 0xFFFF) + (checksum_val >> 16)

    checksum_val = ~checksum_val & 0xFFFF
    return checksum_val


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
    sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sender_socket.bind(("192.168.64.17", PORT))

    sender = PASender(sender_socket, config_file="./config.txt")
    with open(src_filename, "rb") as file:
        file_content = file.read()

    seq_num = 0
    chunks = [file_content[i : i + 1024] for i in range(0, len(file_content), 1024)]
    for chunk in chunks:
        sending_checksum = checksum(chunk)
        packet = bytes([seq_num]) + sending_checksum.to_bytes(2, "big") + chunk
        sender.sendto_bytes(packet, (dst_addr, PORT))
        logger.writePkt(seq_num, logger.SEND_DATA)

        while True:
            ack_packet, _ = sender_socket.recvfrom(4)
            received_ack_num = ack_packet[0]

            if received_ack_num == seq_num:
                logger.writePkt(seq_num, logger.SUCCESS_ACK)
                break
            else:
                ack_num = (received_ack_num + 1) % 2
                logger.writeAck(ack_num, logger.WRONG_SEQ_NUM)
                sender.sendto_bytes(packet, (dst_addr, PORT))
                logger.writePkt(seq_num, logger.SEND_DATA_AGAIN)

        seq_num = 1 - seq_num

    end_packet = b"END"
    sender.sendto_bytes(end_packet, (dst_addr, PORT))
    logger.writeEnd()
    sender_socket.close()
