import time
import threading
import sys
import termios
import tty
import select
import yaml

class KeyboardReader:

    def __init__(self,callback=None):
        print("CTOR Keyboard Reader")
        self.callback=callback

    def readKeyboard(self):
        self.fd = sys.stdin.fileno()
        self.old = termios.tcgetattr(self.fd)
        tty.setcbreak(self.fd)
        self.readNext=True
        try:
            if select.select([sys.stdin], [], [], 0.05)[0]:
                self.ch=sys.stdin.read(1)
                self.status=self.callback(self.ch)
        finally:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)


    callback=None
    status=None
    ch=None
    fd=None
    old=None
    readNext=True
