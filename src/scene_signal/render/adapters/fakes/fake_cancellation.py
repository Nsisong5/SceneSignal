from scene_signal.render.ports.cancellation import CancellationToken

class FakeCancellationToken(CancellationToken):
    def __init__(self, cancelled: bool = False) -> None:
        self._cancelled = cancelled

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled

    def raise_if_cancelled(self) -> None:
        if self._cancelled:
            raise RuntimeError("Render cancelled")
