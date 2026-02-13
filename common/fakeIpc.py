import threading
import queue

class FakeIpcMessage:
    def __init__(self, msg, listenerId, senderId):
        self._msg = msg
        self._listenerId = listenerId
        self._senderId = senderId 

class FakeIpc:
    def __init__(self, listeners: dict, queue_size=1):
        self.listenerList = listeners
        self.queues = {}
        self.workers = []

        for name, listener in listeners.items():
            q = queue.Queue(maxsize=queue_size)
            self.queues[name] = q

            t = threading.Thread(
                target=self._worker,
                args=(listener, q),
                daemon=True
            )
            t.start()
            self.workers.append(t)

    def _worker(self, listener, q: queue.Queue):
        while True:
            msg = q.get()
            try:
                listener.receive(msg)
            finally:
                q.task_done()

    def send(self, msg: FakeIpcMessage):
        q = self.queues.get(msg._listenerId)
        if q is None:
            raise KeyError(f"No listener named '{msg._listenerId}'")

        q.put(msg)   # blocks if queue full (backpressure)

    def wait(self):
        """Block until all queued messages have been processed."""
        for q in self.queues.values():
            q.join()
