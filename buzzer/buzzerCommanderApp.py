# buzzerCommanderApp.py
#================================================================
# Buzzer Commander App
# Listens for string commands and plays droid sounds
#================================================================
import time
from pathlib import Path

#=================================================================
# Custom System
#=================================================================
from remote.common.listenerApp import Listener
from remote.buzzer.droid_sounds import DroidSpeaker

from remote.common.pythonIpcManager import pythonIpcManager as ipc

#=================================================================
# Setup Droid Speaker
#=================================================================
droid = DroidSpeaker(speed=1.2)

#=================================================================
# Command Processor - Just say whatever string is received
#=================================================================
def processCmd(data):
    print(f"Buzzer saying: '{data}'")
    droid.say(data)

#=================================================================
# Main Listener Loop
#=================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Buzzer Commander App Started")
    print("Listening for text at /tmp/buzzerLoop")
    print("Each character will be converted to droid sounds")
    print("=" * 60)
    
    # Startup sound
    droid.say("READY")
    
    # Create listener
    l = Listener("/tmp/buzzerLoop", processCmd)
    
    try:
        l.processQueue()
    except KeyboardInterrupt:
        print("\nShutting down buzzer commander...")
        droid.say("BYE")
        droid.close()
    except Exception as e:
        print(f"Error: {e}")
        droid.worried("ERROR")
        droid.close()
