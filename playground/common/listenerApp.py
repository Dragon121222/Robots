# ================================================================
# Imports
# ================================================================

import os
import socket
import pickle

try:
    from robot_hat import Servo
except Exception:
    from robot_hat.servo import Servo


# ================================================================
# Listener
# ================================================================

def defaultCmd(data):
    print("Command Received:", data)

class Listener:
    def __init__(self, path="/tmp/loopBack", callBack=defaultCmd):
        self.path = path
        self.cb = callBack

        if os.path.exists(self.path):
            os.unlink(self.path)

        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.sock.bind(self.path)

        print("Listening on", self.path)

    def processQueue(self):
        print("Waiting for new command...")
        while True:
            msg = self.sock.recv(4096)
            try:
                cmd = pickle.loads(msg)
            except Exception:
                cmd = msg.decode(errors="ignore")

            print("New message:", cmd)
            self.handle(cmd)

    def handle(self, cmd):
        self.cb(cmd)

# ================================================================
# Main
# ================================================================

if __name__ == "__main__":
    l = Listener("/tmp/loopBack")
    l.processQueue()

