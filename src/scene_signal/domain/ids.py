"""ID allocator for generating sequential prefixed IDs like shot-001."""


class IdAllocator:
    """Generates zero-padded IDs with widening support beyond 999."""

    def __init__(self, prefix: str):
        self.prefix = prefix
        self._counter = 0

    def next_id(self) -> str:
        self._counter += 1
        n = self._counter
        if n < 1000:
            return f"{self.prefix}-{n:03d}"
        return f"{self.prefix}-{n}"

    def reset(self) -> None:
        self._counter = 0
