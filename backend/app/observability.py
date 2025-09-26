import time, uuid
import structlog

logger = structlog.get_logger()

class Trace:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.start = time.perf_counter()
    def end_ms(self):
        return int((time.perf_counter() - self.start) * 1000)
