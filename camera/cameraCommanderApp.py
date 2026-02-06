# cameraCommanderApp.py
#================================================================
# Camera Commander App
# Listens for commands and captures images from /dev/video1
# Sends frames via Unix socket to /tmp/cameraFrames
#================================================================
import cv2
import time
import threading
import pickle
import socket
import os
from pathlib import Path
from datetime import datetime

#=================================================================
# Custom System
#=================================================================
from remote.common.listenerApp import Listener

#=================================================================
# Configuration
#=================================================================
CAMERA_DEVICE = "/dev/video1"
CAMERA_SOCKET = "/tmp/cameraFrames"
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CONTINUOUS_FPS = 10  # Frames per second for continuous mode

#=================================================================
# Camera Manager
#=================================================================
class CameraManager:
    def __init__(self, device=CAMERA_DEVICE):
        self.device = device
        self.camera = None
        self.continuous_mode = False
        self.continuous_thread = None
        self.save_to_disk = False
        
        # Socket for sending frames (STREAM for large images)
        self.server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        
        # Remove old socket if exists
        if os.path.exists(CAMERA_SOCKET):
            os.remove(CAMERA_SOCKET)
        
        # Bind and listen
        self.server_sock.bind(CAMERA_SOCKET)
        self.server_sock.listen(5)
        
        # Track connected clients
        self.clients = []
        
        print(f"Camera: ✓ Camera socket ready at {CAMERA_SOCKET}")
        
        # Initialize camera
        self.open_camera()
        
    def open_camera(self):
        """Open the camera device"""
        try:
            # self.camera = cv2.VideoCapture(self.device)

            self.camera = cv2.VideoCapture("/dev/video1", cv2.CAP_V4L2)

            # Force MJPG (critical)
            self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))

            #Valid Options
            #352x288

            # Choose sane vision defaults
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)

            # Optional but recommended: reduce latency
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if not self.camera.isOpened():
                raise RuntimeError(f"Failed to open camera {self.device}")
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            
            print(f"Camera: ✓ Camera opened: {self.device}")
            print(f"Camera:   Resolution: {CAMERA_WIDTH}x{CAMERA_HEIGHT}")
            
            # Warm up camera
            for _ in range(5):
                self.camera.read()
                
        except Exception as e:
            print(f"Camera: ✗ Failed to open camera: {e}")
            raise

    def save_image_to_disk(self, frame, directory="/tmp/camera_snaps"):
        """Save a captured frame to disk as a JPEG"""
        Path(directory).mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"snapshot_{timestamp}.jpg"
        filepath = Path(directory) / filename
        
        cv2.imwrite(str(filepath), frame)
        return filepath

    def capture_single_image(self):
        """Capture a single image and send via socket"""
        if not self.camera or not self.camera.isOpened():
            print("Camera: ✗ Camera not available")
            return False
        
        try:
            ret, frame = self.camera.read()
            if not ret:
                print("Camera: ✗ Failed to capture image")
                return False

            # Optionally save to disk
            if self.save_to_disk:
                saved_path = self.save_image_to_disk(frame)
                print(f"Camera: ✓ Image saved to {saved_path}")

            # Encode as JPEG
            _, encoded = cv2.imencode('.jpg', frame)
            image_data = {
                'timestamp': time.time(),
                'image': encoded.tobytes(),
                'width': frame.shape[1],
                'height': frame.shape[0]
            }
            
            # Send to all connected clients
            data = pickle.dumps(image_data)
            data_size = len(data).to_bytes(4, 'big')  # Send size first
            
            for client in self.clients[:]:  # Copy list to allow removal
                try:
                    client.sendall(data_size + data)
                except:
                    self.clients.remove(client)
                    client.close()
            
            print(f"Camera: ✓ Image captured and sent to {len(self.clients)} client(s)")
            return True
            
        except Exception as e:
            print(f"Camera: ✗ Error capturing image: {e}")
            return False
    
    def start_continuous_capture(self):
        """Start continuous image capture"""
        if self.continuous_mode:
            print("Camera: ⚠ Continuous mode already running")
            return
        
        self.continuous_mode = True
        self.continuous_thread = threading.Thread(target=self._continuous_capture_loop, daemon=True)
        self.continuous_thread.start()
        print(f"Camera: ✓ Started continuous capture at {CONTINUOUS_FPS} fps")
    
    def stop_continuous_capture(self):
        """Stop continuous image capture"""
        if not self.continuous_mode:
            print("Camera: ⚠ Continuous mode not running")
            return
        
        self.continuous_mode = False
        if self.continuous_thread:
            self.continuous_thread.join(timeout=2.0)
        print("Camera: ✓ Stopped continuous capture")
    
    def _continuous_capture_loop(self):
        """Continuous capture loop (runs in separate thread)"""
        frame_delay = 1.0 / CONTINUOUS_FPS
        frame_count = 0
        
        while self.continuous_mode:
            try:
                ret, frame = self.camera.read()
                if not ret:
                    print("Camera: ✗ Failed to capture frame")
                    time.sleep(0.1)
                    continue
                
                # Encode as JPEG
                _, encoded = cv2.imencode('.jpg', frame)
                image_data = {
                    'timestamp': time.time(),
                    'image': encoded.tobytes(),
                    'width': frame.shape[1],
                    'height': frame.shape[0],
                    'frame_count': frame_count
                }
                
                # Send to all connected clients
                data = pickle.dumps(image_data)
                data_size = len(data).to_bytes(4, 'big')  # Send size first
                
                for client in self.clients[:]:  # Copy list to allow removal
                    try:
                        client.sendall(data_size + data)
                    except:
                        self.clients.remove(client)
                        client.close()
                
                frame_count += 1
                time.sleep(frame_delay)
                
            except Exception as e:
                print(f"Camera: ✗ Error in continuous capture: {e}")
                time.sleep(0.1)
    
    def start_accepting_clients(self):
        """Start thread to accept client connections"""
        def accept_loop():
            while True:
                try:
                    client, addr = self.server_sock.accept()
                    self.clients.append(client)
                    print(f"Camera: ✓ Client connected (total: {len(self.clients)})")
                except:
                    break
        
        accept_thread = threading.Thread(target=accept_loop, daemon=True)
        accept_thread.start()
    
    def close(self):
        """Release camera resources"""
        self.stop_continuous_capture()
        
        # Close all client connections
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        
        # Close server socket
        try:
            self.server_sock.close()
        except:
            pass
        
        # Remove socket file
        if os.path.exists(CAMERA_SOCKET):
            os.remove(CAMERA_SOCKET)
        
        # Release camera
        if self.camera:
            self.camera.release()
            print("Camera: ✓ Camera released")


#=================================================================
# Setup Camera Manager
#=================================================================
camera = CameraManager()

#=================================================================
# Command Processor
#=================================================================
def processCmd(data):
    """Process camera commands"""
    print(f"Camera: Camera Command: '{data}'")
    
    cmd = str(data).strip().lower()
    
    if cmd == "capture" or cmd == "snap" or cmd == "photo":
        camera.capture_single_image()
        
    elif cmd == "start" or cmd == "record" or cmd == "continuous":
        camera.start_continuous_capture()
        
    elif cmd == "stop" or cmd == "pause" or cmd == "end":
        camera.stop_continuous_capture()
        
    elif cmd == "save":
        camera.save_to_disk = True
        print("Camera: ✓ Disk saving enabled")
        
    elif cmd == "nosave":
        camera.save_to_disk = False
        print("Camera: ✓ Disk saving disabled")
        
    elif cmd == "status":
        mode = "CONTINUOUS" if camera.continuous_mode else "IDLE"
        save = "ON" if camera.save_to_disk else "OFF"
        print(f"Camera: Status: {mode} | Save: {save}")
        
    else:
        print(f"Camera: ⚠ Unknown command: {data}")
        print("Camera: Valid: capture, start, stop, save, nosave, status")

#=================================================================
# Main Entry Point
#=================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Camera: Camera Commander App")
    print("=" * 60)
    print(f"Camera: Device: {CAMERA_DEVICE}")
    print(f"Camera: Output socket: {CAMERA_SOCKET}")
    print(f"Camera: Resolution: {CAMERA_WIDTH}x{CAMERA_HEIGHT}")
    print(f"Camera: Continuous FPS: {CONTINUOUS_FPS}")
    print("=" * 60)
    print("\nCamera: Commands:")
    print("Camera:   capture/snap/photo - Take single image")
    print("Camera:   start/record/continuous - Start continuous capture")
    print("Camera:   stop/pause/end - Stop continuous capture")
    print("Camera:   save - Enable saving to disk")
    print("Camera:   nosave - Disable saving to disk")
    print("Camera:   status - Report current mode")
    print("=" * 60)
    
    print("==================================================================")
    print("Activate Camera App")
    print("==================================================================")

    # Create listener
    l = Listener("/tmp/cameraLoop", processCmd)
    
    # Start accepting client connections
    camera.start_accepting_clients()
    
    try:
        print("\nCamera: Listening for commands...\n")
        l.processQueue()
    except KeyboardInterrupt:
        print("\n\nCamera: Shutting down camera commander...")
        camera.close()
    except Exception as e:
        print(f"Camera: Error: {e}")
        camera.close()