import base64
import sys
import time
import zlib
from pathlib import Path

import cv2
import qrcode
from pyzbar.pyzbar import decode

sys.path.append(str(Path(__file__).parent.parent))  # Add src to Python path
from camera.camera_client import CameraClient

PROJECT_ROOT = Path(__file__).parent.parent.parent


class Receiver:
    PACKET_SIZE = 1024
    CHECKSUM_SIZE = 4
    SEQ_NUM_FIELD_SIZE = 1
    NUM_SEQS = 2 ** (8 * SEQ_NUM_FIELD_SIZE)
    N = NUM_SEQS - 2
    DATA_SIZE = PACKET_SIZE - CHECKSUM_SIZE - SEQ_NUM_FIELD_SIZE

    def __init__(self):
        self.http_outgoing = PROJECT_ROOT / "data" / "app" / "out"
        self.http_incoming = PROJECT_ROOT / "data" / "app" / "in"
        self.printing_dir = PROJECT_ROOT / "data" / "transport" / "printing"

        self.http_outgoing.mkdir(parents=True, exist_ok=True)
        self.http_incoming.mkdir(parents=True, exist_ok=True)
        self.printing_dir.mkdir(parents=True, exist_ok=True)

        self.camera_client = CameraClient()

        self.expected_seq_num = 0

    def qr_print(self, packet, ack_num):
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

        qr_image.save(self.printing_dir / f"ack_{ack_num}.png")

    def send_ack(self, ack):
        packet = bytearray()
        ack = ack.to_bytes(1, sys.byteorder)
        checksum = zlib.crc32(ack).to_bytes(4, sys.byteorder)

        packet.extend(checksum)
        packet.extend(ack)

        self.qr_print(packet, int.from_bytes(ack, sys.byteorder))

    def recv_packet(self):
        print("Scanning for packet... Press 'q' to quit")
        try:
            while True:
                frame = self.camera_client.get_frame()

                cv2.imshow("Receiver", frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

                qr_codes = decode(frame)
                for qr in qr_codes:
                    packet = base64.b64decode(qr.data.decode("ascii"))

                    print("packet", packet)

                    checksum_from_packet = int.from_bytes(
                        packet[: self.CHECKSUM_SIZE], sys.byteorder
                    )
                    content = packet[self.CHECKSUM_SIZE :]
                    print()
                    print("content", content)
                    print()

                    if zlib.crc32(content) != checksum_from_packet:
                        return True, None, None

                    seq_num = int.from_bytes(
                        content[: self.SEQ_NUM_FIELD_SIZE], sys.byteorder
                    )
                    data = content[self.SEQ_NUM_FIELD_SIZE :]

                    return False, seq_num, data

        except Exception as e:
            print(f"Error reading from camera: {e}")
            return True, None, None

        return True, None, None

    def write_to_http_incoming(self, data):
        with open(self.http_incoming / "request_.json", "ab") as f:
            f.write(data)
            f.flush()

    def run(self):
        try:
            last_ack = None

            while True:
                corrupt, seq_num, data = self.recv_packet()
                print("received packet")

                if corrupt:
                    print("corrupt packet")
                    if last_ack is not None:
                        self.send_ack(last_ack)
                    continue

                if seq_num != self.expected_seq_num:
                    print("out of order packet")
                    if last_ack is not None:
                        self.send_ack(last_ack)
                    continue

                self.send_ack(self.expected_seq_num)
                print("sent ack")
                last_ack = self.expected_seq_num
                self.expected_seq_num = (self.expected_seq_num + 1) % self.NUM_SEQS

                print("i am writing!!")
                self.write_to_http_incoming(data)
        finally:
            self.camera_client.close()
            cv2.destroyAllWindows()


def main():
    recv = Receiver()
    recv.run()


if __name__ == "__main__":
    main()
