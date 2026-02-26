import socket
import pickle

#=================================================================
# Custom System
#=================================================================
from remote.keyboard.keyboardReader import KeyboardReader

sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

lastInput=""
currentInput=""

def multiplexer(input):
    global currentInput
    global lastInput
    returnValue=""
    print(input, end="", flush=True)

    if input != "\n":
        currentInput=currentInput + input
    else:
        print("Command Received: ", currentInput)
        if currentInput == "quit":
            print("Exiting program.")
            returnValue="quit"
        if currentInput == "snap":
            sock.sendto(pickle.dumps(currentInput), "/tmp/buzzerLoop")
            sock.sendto(pickle.dumps(currentInput), "/tmp/cameraLoop")
        else:
            sock.sendto(pickle.dumps(currentInput), "/tmp/loopBack")
            sock.sendto(pickle.dumps(currentInput), "/tmp/buzzerLoop")
        lastInput=currentInput
        currentInput=""

        print("\n")

    if returnValue != "":
        return returnValue




kr = KeyboardReader(multiplexer)

while kr.status != "quit":
    kr.readKeyboard()
