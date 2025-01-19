import sys
import time
import zlib
from collections import deque
from itertools import chain
from pathlib import Path
import base64

import cv2
import qrcode
from pyzbar.pyzbar import decode

sys.path.append(str(Path(__file__).parent.parent))  # Add src to Python path
from camera.camera_client import CameraClient

PROJECT_ROOT = Path(__file__).parent.parent.parent


class Sender:
    PACKET_SIZE = 1024
    CHECKSUM_SIZE = 4
    SEQ_NUM_FIELD_SIZE = 1
    NUM_SEQS = 2 ** (8 * SEQ_NUM_FIELD_SIZE)
    N = NUM_SEQS - 2
    DATA_SIZE = PACKET_SIZE - CHECKSUM_SIZE - SEQ_NUM_FIELD_SIZE
    TIMEOUT = 6000

    def __init__(self):
        self.http_outgoing = PROJECT_ROOT / "data" / "app" / "out"
        self.http_incoming = PROJECT_ROOT / "data" / "app" / "in"
        self.printing_dir = PROJECT_ROOT / "data" / "transport" / "printing"

        self.http_outgoing.mkdir(parents=True, exist_ok=True)
        self.http_incoming.mkdir(parents=True, exist_ok=True)
        self.printing_dir.mkdir(parents=True, exist_ok=True)

        self.buffer = dict()
        self.base = 0
        self.next_seq_num = 0

        self.http_outgoing_queue = deque()
        self.processed_files = set()

        self.camera_client = CameraClient()

        self.stop_timer()

    def read_from_http_outgoing(self):
        for file_path in self.http_outgoing.glob("request_*.json"):
            if file_path in self.processed_files:
                continue

            self.processed_files.add(file_path)

            with open(file_path, "rb") as f:
                data = f.read()

            for i in range(0, len(data), self.DATA_SIZE):
                self.http_outgoing_queue.append(data[i : i + self.DATA_SIZE])

    def prepare_packet(self, data, seq_num):
        packet = bytearray()

        seq_num_bytes = seq_num.to_bytes(self.SEQ_NUM_FIELD_SIZE, sys.byteorder)

        seq_plus_data = bytearray()
        seq_plus_data.extend(seq_num_bytes)
        seq_plus_data.extend(data)

        checksum = zlib.crc32(seq_plus_data).to_bytes(4, sys.byteorder)

        packet.extend(checksum)
        packet.extend(seq_plus_data)

        self.buffer[seq_num] = packet

        return packet

    def send_packet(self, seq_num):
        packet = self.buffer[seq_num]
        b64_string = base64.b64encode(packet).decode("ascii")

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(b64_string)
        qr.make(fit=True)

        qr_image = qr.make_image(fill_color="black", back_color="white")
        qr_image.save(self.printing_dir / f"packet_{seq_num}.png")

    def recv_packet(self):
        print("Scanning for ACK code... Press 'q' to quit")

        while not self.is_timeout():
            try:
                frame = self.camera_client.get_frame()

                cv2.imshow("Sender", frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

                qr_codes = decode(frame)

                for qr in qr_codes:
                    packet = qr.data

                    checksum_from_packet = int.from_bytes(
                        packet[: self.CHECKSUM_SIZE], sys.byteorder
                    )

                    ack = packet[self.CHECKSUM_SIZE :]

                    if zlib.crc32(ack) != checksum_from_packet:
                        return True, None

                    return False, int.from_bytes(ack, sys.byteorder)

            except Exception as e:
                print(f"Error reading from camera: {e}")
                return True, None

        raise TimeoutError("Timeout waiting for ACK")

    def start_timer(self):
        self.cutoff = time.time() + self.TIMEOUT

    def stop_timer(self):
        self.cutoff = 1e9 + time.time()

    def is_timeout(self):
        return time.time() > self.cutoff

    def run(self):
        try:
            last_iter = False

            while True:
                try:
                    window = {
                        i % self.NUM_SEQS for i in range(self.base, self.base + self.N)
                    }
                    while self.next_seq_num in window:
                        print("i am reading from http outgoing")
                        self.read_from_http_outgoing()

                        print("http outgoing queue", self.http_outgoing_queue)

                        if len(self.http_outgoing_queue) == 0:
                            last_iter = True
                            break

                        in_data = self.http_outgoing_queue.popleft()

                        self.prepare_packet(in_data, self.next_seq_num)
                        self.send_packet(self.next_seq_num)
                        print("i am sending packet")

                        if self.base == self.next_seq_num:
                            self.start_timer()

                        self.next_seq_num = (self.next_seq_num + 1) % self.NUM_SEQS

                    time.sleep(300)
                    corrupt, ack = self.recv_packet()

                    if corrupt:
                        continue

                    self.base = (ack + 1) % self.NUM_SEQS
                    if self.base == self.next_seq_num:
                        self.stop_timer()
                        if last_iter:
                            break
                    else:
                        self.start_timer()

                except TimeoutError:
                    self.start_timer()

                    for i in range(
                        self.base,
                        (
                            self.next_seq_num
                            if self.next_seq_num >= self.base
                            else self.next_seq_num + self.NUM_SEQS
                        ),
                    ):
                        j = i % self.NUM_SEQS
                        self.send_packet(j)
        finally:
            self.camera_client.close()
            cv2.destroyAllWindows()


def main():
    sender = Sender()
    sender.run()


if __name__ == "__main__":
    main()
