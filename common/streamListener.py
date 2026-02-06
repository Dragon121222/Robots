import os
import socket
import pickle
import struct
import threading

class StreamListener:
    """
    Stream-based UNIX socket listener with length-prefixed messages.
    Each message is a pickle object.
    """

    def __init__(self, path, callback=None):
        self.path = path
        self.cb = callback
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        # Determine if acting as server or client
        if os.path.exists(path):
            # Try to connect as client
            try:
                self.sock.connect(path)
                self._is_client = True
                print(f"Connected to server socket at {path}")
            except Exception as e:
                raise RuntimeError(f"Failed to connect to server at {path}: {e}")
        else:
            # Bind as server
            self.sock.bind(path)
            self.sock.listen(1)
            self._is_client = False
            print(f"Listening as server at {path}")

        self.running = False

    def _recv_exact(self, conn, n):
        data = b""
        while len(data) < n:
            chunk = conn.recv(n - len(data))
            if not chunk:
                raise ConnectionError("Socket closed unexpectedly")
            data += chunk
        return data

    def _handle_connection(self, conn):
        """Process incoming stream connection"""
        try:
            while True:
                # Read length prefix
                hdr = self._recv_exact(conn, 4)
                msg_len = struct.unpack("!I", hdr)[0]

                # Read message data
                data = self._recv_exact(conn, msg_len)

                try:
                    obj = pickle.loads(data)
                except Exception:
                    obj = data.decode(errors="ignore")

                if self.cb:
                    self.cb(obj)

        except ConnectionError:
            pass
        finally:
            conn.close()

    def processQueue(self):
        """Main loop"""
        self.running = True
        if self._is_client:
            while self.running:
                try:
                    # Client just reads from server socket
                    self._handle_connection(self.sock)
                except Exception as e:
                    print(f"StreamListener client error: {e}")
                    # Reconnect logic could go here
                    break
        else:
            while self.running:
                conn, _ = self.sock.accept()
                threading.Thread(target=self._handle_connection, args=(conn,), daemon=True).start()

    def stop(self):
        self.running = False
        self.sock.close()
