"""Timeline domain primitives: TimeUs, Interval, and time helpers."""

from decimal import ROUND_HALF_EVEN, Decimal
from fractions import Fraction
from typing import Sequence, Union


class TimeUs:
    """Integer microseconds representing time non-negatively."""

    def __init__(self, microseconds: int):
        if microseconds < 0:
            raise ValueError("TimeUs cannot be negative")
        self._us = int(microseconds)

    @property
    def microseconds(self) -> int:
        return self._us

    @classmethod
    def from_seconds_decimal(cls, val: Union[str, Decimal, int, float]) -> "TimeUs":
        if isinstance(val, float):
            return cls.from_float_seconds(val)
        dec = Decimal(str(val))
        us = (dec * Decimal("1000000")).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN)
        return cls(int(us))

    @classmethod
    def from_float_seconds(cls, seconds: float) -> "TimeUs":
        if seconds < 0:
            raise ValueError("Time cannot be negative")
        dec = Decimal(str(seconds))
        us = (dec * Decimal("1000000")).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN)
        return cls(int(us))

    @classmethod
    def from_pts(cls, pts: int, time_base: Union[Fraction, str]) -> "TimeUs":
        if isinstance(time_base, str):
            parts = time_base.split("/")
            if len(parts) == 2:
                tb = Fraction(int(parts[0]), int(parts[1]))
            else:
                tb = Fraction(time_base)
        else:
            tb = time_base
        seconds = Fraction(pts) * tb
        us = (Decimal(seconds.numerator) / Decimal(seconds.denominator) * Decimal("1000000")).quantize(
            Decimal("1"), rounding=ROUND_HALF_EVEN
        )
        return cls(int(us))

    def to_seconds(self) -> float:
        dec = Decimal(self._us) / Decimal("1000000")
        quantized = dec.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
        return float(quantized)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TimeUs):
            return NotImplemented
        return self._us == other._us

    def __lt__(self, other: "TimeUs") -> bool:
        return self._us < other._us

    def __le__(self, other: "TimeUs") -> bool:
        return self._us <= other._us

    def __gt__(self, other: "TimeUs") -> bool:
        return self._us > other._us

    def __ge__(self, other: "TimeUs") -> bool:
        return self._us >= other._us

    def __add__(self, other: Union["TimeUs", int]) -> "TimeUs":
        val = other.microseconds if isinstance(other, TimeUs) else other
        return TimeUs(self._us + val)

    def __sub__(self, other: Union["TimeUs", int]) -> "TimeUs":
        val = other.microseconds if isinstance(other, TimeUs) else other
        return TimeUs(self._us - val)

    def __hash__(self) -> int:
        return hash(self._us)

    def __repr__(self) -> str:
        return f"TimeUs({self._us}us = {self.to_seconds()}s)"


class Interval:
    """Half-open time interval [start, end) in microseconds."""

    def __init__(self, start: TimeUs, end: TimeUs):
        if end <= start:
            raise ValueError("Interval end must be strictly greater than start")
        self.start = start
        self.end = end

    @property
    def duration_us(self) -> int:
        return self.end.microseconds - self.start.microseconds

    def duration_seconds(self) -> float:
        return self.end.to_seconds() - self.start.to_seconds()

    def contains(self, t: TimeUs) -> bool:
        return self.start <= t < self.end

    def overlaps(self, other: "Interval") -> bool:
        return self.start < other.end and other.start < self.end

    def is_adjacent_to(self, other: "Interval") -> bool:
        return self.end == other.start or other.end == self.start

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Interval):
            return NotImplemented
        return self.start == other.start and self.end == other.end

    def __repr__(self) -> str:
        return f"Interval([{self.start.to_seconds()}, {self.end.to_seconds()}])"


def tile_check(intervals: Sequence[Interval], total_duration: TimeUs) -> bool:
    """Verify that intervals tile [0, total_duration) without gaps or overlaps."""
    if not intervals:
        return total_duration.microseconds == 0

    sorted_ivs = sorted(intervals, key=lambda iv: iv.start.microseconds)
    if sorted_ivs[0].start.microseconds != 0:
        return False
    if sorted_ivs[-1].end != total_duration:
        return False

    for i in range(len(sorted_ivs) - 1):
        if sorted_ivs[i].end != sorted_ivs[i + 1].start:
            return False
    return True


def snap_to_nearest(t: TimeUs, candidates: Sequence[TimeUs]) -> TimeUs:
    """Return the candidate TimeUs closest to t."""
    if not candidates:
        return t
    return min(candidates, key=lambda c: abs(c.microseconds - t.microseconds))
