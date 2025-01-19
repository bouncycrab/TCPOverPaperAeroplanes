import cv2
import numpy as np
import socket
import pickle
import struct

class CameraClient:
    def __init__(self, host='localhost', port=5000):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))
        self.data = b""
        self.payload_size = struct.calcsize("L")
        
    def get_frame(self):
        while len(self.data) < self.payload_size:
            self.data += self.client_socket.recv(4096)
            
        packed_msg_size = self.data[:self.payload_size]
        self.data = self.data[self.payload_size:]
        msg_size = struct.unpack("L", packed_msg_size)[0]
        
        while len(self.data) < msg_size:
            self.data += self.client_socket.recv(4096)
            
        frame_data = self.data[:msg_size]
        self.data = self.data[msg_size:]
        
        return pickle.loads(frame_data)
        
    def close(self):
        self.client_socket.close()