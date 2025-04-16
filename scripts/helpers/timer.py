import time


class Timer:
    def __init__(self) -> None:
        self._start_time = time.monotonic()

    def elapsed(self) -> float:
        current_monotonic_time = time.monotonic()
        return current_monotonic_time - self._start_time
