import socket
import pickle

sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
sock.sendto(pickle.dumps("Sit"), "/tmp/loopBack")

