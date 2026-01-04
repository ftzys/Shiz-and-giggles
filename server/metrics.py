import logging
import threading
import time
from collections import Counter
from typing import Dict


class Metrics:
    """
    Minimal metrics sink with periodic logging.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counter = Counter()

    def increment(self, key: str, value: int = 1) -> None:
        with self._lock:
            self._counter[key] += value

    def snapshot(self) -> Dict[str, int]:
        with self._lock:
            return dict(self._counter)

    def log_periodically(self, interval_seconds: int, stop_event: threading.Event) -> None:
        while not stop_event.wait(interval_seconds):
            snapshot = self.snapshot()
            logging.info("metrics snapshot: %s", snapshot)
