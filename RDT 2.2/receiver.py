import socket
import sys
from logHandler import logHandler


def checksum(received_data):
    if len(received_data) % 2:
        received_data += b"\0"

    checksum_val = 0
    for i in range(0, len(received_data), 2):
        current_word = (received_data[i] << 8) | received_data[i + 1]
        checksum_val += current_word
        checksum_val = (checksum_val & 0xFFFF) + (checksum_val >> 16)

    return checksum_val & 0xFFFF


if __name__ == "__main__":
    try:
        res_filename = sys.argv[1]  # result file name
        log_filename = sys.argv[2]  # log file name
    except IndexError:
        print("How To Use")
        print("python receiver.py <result file name> <log file name>")
        sys.exit(1)

    logger = logHandler()
    logger.startLogging(log_filename)

    PORT = 10090
    receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiver_socket.bind(("192.168.64.21", PORT))

    expected_seq_num = 0

    with open(res_filename, "wb") as file:
        i = 0  ##
        while True:
            packet, addr = receiver_socket.recvfrom(1027)
            if packet == b"END":
                last_packet = expected_seq_num.to_bytes(1, "big")  ##
                receiver_socket.sendto(last_packet, addr)  ##
                break

            received_seq_num = packet[0]
            received_checksum = int.from_bytes(packet[1:3], "big")
            received_data = packet[3:]
            calculated_checksum = checksum(received_data)

            ack_num = None
            if received_seq_num == 0 or received_seq_num == 1:
                ack_num = (received_seq_num + 1) % 2
            else:
                ack_num = received_seq_num % 2

            if received_checksum + calculated_checksum == 0xFFFF:
                if received_seq_num == expected_seq_num:
                    file.write(received_data)
                    i += 1
                    expected_seq_num = 1 - expected_seq_num
                    ack_packet = received_seq_num.to_bytes(1, "big") + b"ACK"
                    receiver_socket.sendto(ack_packet, addr)
                    logger.writeAck(received_seq_num, logger.SEND_ACK)
                else:
                    logger.writeAck(received_seq_num, logger.WRONG_SEQ_NUM)
                    ack_packet = received_seq_num.to_bytes(1, "big") + b"ACK"
                    receiver_socket.sendto(ack_packet, addr)
                    logger.writeAck(received_seq_num, logger.SEND_ACK_AGAIN)
            else:
                logger.writeAck(received_seq_num, logger.CORRUPTED)
                ack_packet = ack_num.to_bytes(1, "big") + b"ACK"
                receiver_socket.sendto(ack_packet, addr)
                if i == 0:
                    logger.writeAck(ack_num, logger.SEND_ACK)
                else:
                    logger.writeAck(ack_num, logger.SEND_ACK_AGAIN)

    logger.writeEnd()
    receiver_socket.close()
