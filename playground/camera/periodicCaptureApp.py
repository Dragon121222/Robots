import socket
import pickle
import time

#=================================================================
# Custom System
#=================================================================
from remote.common.listenerApp import Listener


def commandSnap():
    print("Periodic: Trying to command Snap!")
    sock.sendto(pickle.dumps("snap"), "/tmp/cameraLoop")
    print("Waiting on next call.")

def processCmd(data):
    print("Periodic: Command Complete")
    time.sleep(0.1)
    commandSnap()

sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
time.sleep(10)

print("==================================================================")
print("Activate Periodic App")
print("==================================================================")

l = Listener("/tmp/periodicCmdComplete",processCmd)


commandSnap()
time.sleep(0.1)
commandSnap()
time.sleep(0.1)
commandSnap()
time.sleep(0.1)

l.processQueue()



