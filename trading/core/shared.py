import threading
import time
from collections import deque

class APIThrottle:
    """Enterprise Rate Limitation (Gold Pattern)."""
    def __init__(self, cpm=30):
        self.calls = deque()
        self.limit = cpm
        self.lock = threading.Lock()
    def acquire(self):
        """Acquire a token, blocking if the limit is reached."""
        while True:
            with self.lock:
                now = time.time()
                # Remove calls older than 60 seconds
                while self.calls and self.calls[0] < now - 60:
                    self.calls.popleft()
                if len(self.calls) < self.limit:
                    self.calls.append(now)
                    return True
            # Sleep outside the lock to allow other threads to progress
            time.sleep(0.5)

# Global singleton to ensure both bot and AI tools share the same 30 CPM limit
enterprise_throttle = APIThrottle(30)
