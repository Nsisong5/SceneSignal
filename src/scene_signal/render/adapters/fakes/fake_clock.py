from datetime import datetime
from scene_signal.render.ports.clock import Clock

class FakeClock(Clock):
    def __init__(self, fixed_time: datetime | None = None) -> None:
        self._fixed_time = fixed_time or datetime(2026, 10, 12, 12, 0, 0)

    def now(self) -> datetime:
        return self._fixed_time
