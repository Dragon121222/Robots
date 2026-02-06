# import posix_ipc
# import pickle
# import threading
# from multiprocessing import shared_memory
# import numpy as np


# class pythonIpcManager:
#     _listeners = {}

#     INLINE_LIMIT = 8 * 1024  # bytes

#     @staticmethod
#     def sendMsg(msg, ipcChannelName):
#         mq = posix_ipc.MessageQueue(
#             ipcChannelName,
#             flags=posix_ipc.O_CREAT
#         )

#         # ---- Large NumPy / tensor path ----
#         if isinstance(msg, np.ndarray):
#             shm = shared_memory.SharedMemory(create=True, size=msg.nbytes)
#             np.ndarray(msg.shape, dtype=msg.dtype, buffer=shm.buf)[:] = msg

#             payload = {
#                 "type": "shm",
#                 "shm_name": shm.name,
#                 "shape": msg.shape,
#                 "dtype": str(msg.dtype),
#                 "nbytes": msg.nbytes,
#             }

#             mq.send(pickle.dumps(payload))
#             mq.close()
#             return

#         # ---- Small message path ----
#         data = pickle.dumps(msg)
#         if len(data) > pythonIpcManager.INLINE_LIMIT:
#             raise ValueError("Message too large and not a NumPy array")

#         payload = {
#             "type": "inline",
#             "payload": data,
#         }

#         mq.send(pickle.dumps(payload))
#         mq.close()

#     @staticmethod
#     def setupResponseCallback(responseCallback, ipcChannelName):
#         if ipcChannelName in pythonIpcManager._listeners:
#             raise RuntimeError(f"Listener already registered for {ipcChannelName}")

#         mq = posix_ipc.MessageQueue(
#             ipcChannelName,
#             flags=posix_ipc.O_CREAT
#         )

#         def _listener():
#             while True:
#                 raw, _ = mq.receive()
#                 meta = pickle.loads(raw)

#                 # ---- Inline message ----
#                 if meta["type"] == "inline":
#                     msg = pickle.loads(meta["payload"])
#                     responseCallback(msg)

#                 # ---- Shared memory object ----
#                 elif meta["type"] == "shm":
#                     shm = shared_memory.SharedMemory(name=meta["shm_name"])
#                     arr = np.ndarray(
#                         meta["shape"],
#                         dtype=np.dtype(meta["dtype"]),
#                         buffer=shm.buf
#                     ).copy()

#                     shm.close()
#                     shm.unlink()

#                     responseCallback(arr)

#         t = threading.Thread(target=_listener, daemon=True)
#         t.start()

#         pythonIpcManager._listeners[ipcChannelName] = (mq, t)

import socket
import threading
import pickle
import numpy as np
from multiprocessing import shared_memory

INLINE_LIMIT = 8 * 1024  # bytes

class pythonIpcManager:
    _listeners = {}

    @staticmethod
    def sendMsg(msg, ipcChannelName):
        """Send a message to a given IPC channel (socket-based)"""
        # Ensure socket path
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            client.connect(ipcChannelName)
        except FileNotFoundError:
            raise RuntimeError(f"IPC channel '{ipcChannelName}' not available")

        # Large NumPy/tensor path
        if isinstance(msg, np.ndarray):
            shm = shared_memory.SharedMemory(create=True, size=msg.nbytes)
            np.copyto(np.ndarray(msg.shape, dtype=msg.dtype, buffer=shm.buf), msg)

            payload = {
                "type": "shm",
                "shm_name": shm.name,
                "shape": msg.shape,
                "dtype": str(msg.dtype),
                "nbytes": msg.nbytes,
            }

        else:
            data = pickle.dumps(msg)
            if len(data) > INLINE_LIMIT:
                raise ValueError("Message too large and not a NumPy array")
            payload = {
                "type": "inline",
                "payload": data
            }

        serialized = pickle.dumps(payload)
        size_bytes = len(serialized).to_bytes(4, "big")  # prepend length
        client.sendall(size_bytes + serialized)
        client.close()

    @staticmethod
    def setupResponseCallback(responseCallback, ipcChannelName):
        """Start listening on a UNIX socket and call responseCallback(msg) on new messages"""

        if ipcChannelName in pythonIpcManager._listeners:
            raise RuntimeError(f"Listener already registered for {ipcChannelName}")

        # Create server socket
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            server.bind(ipcChannelName)
        except OSError:
            # remove stale socket
            import os
            if os.path.exists(ipcChannelName):
                os.remove(ipcChannelName)
                server.bind(ipcChannelName)
        server.listen(5)

        def _listener():
            while True:
                conn, _ = server.accept()
                try:
                    # read 4-byte length prefix
                    length_bytes = conn.recv(4)
                    if len(length_bytes) < 4:
                        continue
                    size = int.from_bytes(length_bytes, "big")
                    data = b""
                    while len(data) < size:
                        chunk = conn.recv(size - len(data))
                        if not chunk:
                            break
                        data += chunk
                    payload = pickle.loads(data)

                    if payload["type"] == "inline":
                        msg = pickle.loads(payload["payload"])
                        responseCallback(msg)
                    elif payload["type"] == "shm":
                        shm = shared_memory.SharedMemory(name=payload["shm_name"])
                        arr = np.ndarray(payload["shape"], dtype=np.dtype(payload["dtype"]), buffer=shm.buf).copy()
                        shm.close()
                        shm.unlink()
                        responseCallback(arr)
                finally:
                    conn.close()

        t = threading.Thread(target=_listener, daemon=True)
        t.start()

        pythonIpcManager._listeners[ipcChannelName] = (server, t)
