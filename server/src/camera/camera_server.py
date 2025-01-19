import cv2
import numpy as np
import socket
import pickle
import struct
import argparse
from threading import Thread
import logging
import sys

class CameraServer:
    def __init__(self, host='localhost', port=5000, camera_id=0, show_preview=False, resolution=None):
        self.host = host
        self.port = port
        self.camera_id = camera_id
        self.show_preview = show_preview
        self.resolution = resolution
        
        # Setup logging
        self.logger = logging.getLogger('CameraServer')
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        
        # Initialize server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        
        # Initialize camera
        self.camera = cv2.VideoCapture(self.camera_id)
        if not self.camera.isOpened():
            raise RuntimeError(f"Could not open camera {self.camera_id}")
            
        # Set resolution if specified
        if self.resolution:
            width, height = self.resolution
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        self.running = True
        self.clients = []
        
    def start(self):
        """Start the camera server"""
        self.logger.info(f"Starting camera server on {self.host}:{self.port}")
        self.logger.info(f"Camera ID: {self.camera_id}")
        if self.resolution:
            self.logger.info(f"Resolution: {self.resolution[0]}x{self.resolution[1]}")
        
        # Start accepting client connections
        Thread(target=self.accept_clients).start()
        
        # Start preview if enabled
        if self.show_preview:
            Thread(target=self.show_camera_preview).start()
    
    def accept_clients(self):
        """Accept new client connections"""
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                self.logger.info(f"New client connected from {addr}")
                client_thread = Thread(target=self.handle_client, args=(client_socket,))
                client_thread.daemon = True
                client_thread.start()
                self.clients.append((client_socket, client_thread))
            except Exception as e:
                if self.running:  # Only log if not shutting down
                    self.logger.error(f"Error accepting client: {e}")
    
    def show_camera_preview(self):
        """Show local preview of the camera feed"""
        self.logger.info("Starting camera preview")
        while self.running:
            ret, frame = self.camera.read()
            if ret:
                cv2.imshow('Camera Preview', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.logger.info("Preview window closed")
                    break
        
        cv2.destroyAllWindows()
            
    def handle_client(self, client_socket):
        """Handle individual client connection"""
        try:
            while self.running:
                ret, frame = self.camera.read()
                if not ret:
                    self.logger.error("Failed to read from camera")
                    break
                    
                # Serialize frame
                data = pickle.dumps(frame)
                message_size = struct.pack("L", len(data))
                
                # Send frame size followed by frame data
                client_socket.sendall(message_size + data)
                
        except Exception as e:
            self.logger.error(f"Error handling client: {e}")
        finally:
            client_socket.close()
            
    def stop(self):
        """Stop the camera server and cleanup resources"""
        self.logger.info("Stopping camera server")
        self.running = False
        
        # Close all client connections
        for client_socket, _ in self.clients:
            try:
                client_socket.close()
            except:
                pass
        
        # Close server socket
        try:
            self.server_socket.close()
        except:
            pass
        
        # Release camera
        if self.camera is not None:
            self.camera.release()
        
        # Close any remaining windows
        cv2.destroyAllWindows()
        
        self.logger.info("Camera server stopped")
        
    def get_camera_info(self):
        """Get information about the current camera settings"""
        info = {
            'width': int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': int(self.camera.get(cv2.CAP_PROP_FPS)),
            'camera_id': self.camera_id
        }
        return info

def list_available_cameras():
    """List all available camera devices"""
    available_cameras = []
    for i in range(10):  # Check first 10 camera indices
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available_cameras.append(i)
            cap.release()
    return available_cameras

def main():
    parser = argparse.ArgumentParser(description='Camera Server for shared webcam access')
    parser.add_argument('--host', default='localhost', help='Host address to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to listen on')
    parser.add_argument('--camera', type=int, default=0, help='Camera device index to use')
    parser.add_argument('--preview', action='store_true', help='Show camera preview window')
    parser.add_argument('--width', type=int, help='Camera resolution width')
    parser.add_argument('--height', type=int, help='Camera resolution height')
    parser.add_argument('--list-cameras', action='store_true', help='List available cameras and exit')
    parser.add_argument('--info', action='store_true', help='Show camera info and exit')
    
    args = parser.parse_args()
    
    # List available cameras if requested
    if args.list_cameras:
        cameras = list_available_cameras()
        print(f"Available cameras: {cameras}")
        return
    
    # Setup resolution if specified
    resolution = None
    if args.width and args.height:
        resolution = (args.width, args.height)
    
    # Create and start server
    try:
        server = CameraServer(
            host=args.host,
            port=args.port,
            camera_id=args.camera,
            show_preview=args.preview,
            resolution=resolution
        )
        
        # Show camera info if requested
        if args.info:
            info = server.get_camera_info()
            print("Camera Information:")
            for key, value in info.items():
                print(f"{key}: {value}")
            server.stop()
            return
        
        # Start the server
        server.start()
        print("Press Enter to stop the server...")
        input()
        
    except KeyboardInterrupt:
        print("\nReceived shutdown signal")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'server' in locals():
            server.stop()

if __name__ == "__main__":
    main()