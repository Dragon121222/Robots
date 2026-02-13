import threading
import queue

class FakeIpcMessage:
    def __init__(self, msg, listenerId, senderId, previous_now=None):
        self._msg = msg
        self._listenerId = listenerId
        self._senderId = senderId 
        self._previous_now = previous_now

class FakeIpc:
    def __init__(self, listeners: dict, queue_size=1, onSend=None, onReceive=None):
        self.listenerList = listeners
        self.queues = {}
        self.workers = []
        self._onSend = onSend
        self._onReceive = onReceive

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
                if self._onReceive != None:
                    self._onReceive(msg)
                listener.receive(msg)
            finally:
                q.task_done()

    def send(self, msg: FakeIpcMessage):
        q = self.queues.get(msg._listenerId)
        if q is None:
            raise KeyError(f"No listener named '{msg._listenerId}'")

        if self._onSend != None:
            self._onSend(msg)
        q.put(msg)   # blocks if queue full (backpressure)

    def wait(self):
        """Block until all queued messages have been processed."""
        for q in self.queues.values():
            q.join()
