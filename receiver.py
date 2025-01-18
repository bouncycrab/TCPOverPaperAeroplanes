import sys
import zlib

import cv2
import qrcode
from pyzbar.pyzbar import decode


class Receiver:
    PACKET_SIZE = 64
    CHECKSUM_SIZE = 4
    SEQ_NUM_FIELD_SIZE = 1
    NUM_SEQS = 2 ** (8 * SEQ_NUM_FIELD_SIZE)
    N = NUM_SEQS - 2
    DATA_SIZE = PACKET_SIZE - CHECKSUM_SIZE - SEQ_NUM_FIELD_SIZE

    def __init__(self, server_port):
        self.expected_seq_num = 0

    def qr_print(self, packet):
        packet = bytes(packet)

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        qr.add_data(packet)
        qr.make(fit=True)

        qr_image = qr.make_image(fill_color="black", back_color="white")

        qr_image.save("test_qr.png")

    def qr_scan(self):
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("Error: Could not open webcam")
            return

        print("Scanning for QR codes... Press 'q' to quit")

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Can't receive frame")
                break

            qr_codes = decode(frame)

            for qr in qr_codes:
                qr_data = qr.data.decode("utf-8")
                print(f"QR Code detected: {qr_data}")

                points = qr.polygon
                if len(points) == 4:
                    pts = [(int(p.x), int(p.y)) for p in points]
                    cv2.polylines(frame, [pts], True, (0, 255, 0), 2)

                    # Add text above the QR code
                    cv2.putText(
                        frame,
                        qr_data,
                        (pts[0][0], pts[0][1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        2,
                    )

            cv2.imshow("QR Code Scanner", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()

    def send_ack(self, ack):
        packet = bytearray()
        ack = ack.to_bytes(1, sys.byteorder)
        checksum = zlib.crc32(ack).to_bytes(4, sys.byteorder)

        packet.extend(checksum)
        packet.extend(ack)

        self.qr_print(packet)

    def recv_packet(self):
        max_size = self.PACKET_SIZE

        packet, self.client_addr = self.socket.recvfrom(max_size)

        if len(packet) == 0:
            raise RuntimeError("Connection broken")

        packet = bytearray(packet)

        checksum_from_packet = int.from_bytes(
            packet[: self.CHECKSUM_SIZE], sys.byteorder
        )
        content = packet[self.CHECKSUM_SIZE :]

        if zlib.crc32(content) != checksum_from_packet:
            return True, None, None

        seq_num = int.from_bytes(content[: self.SEQ_NUM_FIELD_SIZE], sys.byteorder)
        data = content[self.SEQ_NUM_FIELD_SIZE :]

        return False, seq_num, data

    def run(self):
        last_ack = None

        while True:
            corrupt, seq_num, data = self.recv_packet()

            if corrupt:
                if last_ack is not None:
                    self.send_ack(last_ack)
                continue

            if seq_num != self.expected_seq_num:
                if last_ack is not None:
                    self.send_ack(last_ack)
                continue

            self.send_ack(self.expected_seq_num)
            last_ack = self.expected_seq_num
            self.expected_seq_num = (self.expected_seq_num + 1) % self.NUM_SEQS

            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()


def main():
    # bob = Bob(int(sys.argv[1]))
    # bob.run()

    recv = Receiver(1)
    recv.qr_print(b"hello")
    recv.qr_scan()


if __name__ == "__main__":
    main()
