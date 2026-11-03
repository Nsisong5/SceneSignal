"""Unit tests for timeline domain primitives."""

from decimal import Decimal
from fractions import Fraction

import pytest

from scene_signal.domain.timeline import Interval, TimeUs, snap_to_nearest, tile_check


def test_time_us_conversions():
    t1 = TimeUs.from_pts(30030, Fraction(1, 30000))
    assert t1.microseconds == 1001000
    assert t1.to_seconds() == 1.001

    t2 = TimeUs.from_pts(450450, "1/90000")
    assert t2.microseconds == 5005000
    assert t2.to_seconds() == 5.005

    t3 = TimeUs.from_seconds_decimal("5.005000")
    assert t3.microseconds == 5005000

    t4 = TimeUs.from_seconds_decimal(Decimal("0.041708"))
    assert t4.to_seconds() == 0.041708

    # Half-even rounding test
    # 0.0000005 seconds = 0.5 microseconds -> rounds to 0
    t_zero = TimeUs.from_float_seconds(0.0000004)
    assert t_zero.microseconds == 0

    # Negative times rejected
    with pytest.raises(ValueError):
        TimeUs(-1)
    with pytest.raises(ValueError):
        TimeUs.from_float_seconds(-0.1)


def test_interval_operations():
    t0 = TimeUs(0)
    t1 = TimeUs(1000000)
    t2 = TimeUs(2000000)

    iv1 = Interval(t0, t1)
    iv2 = Interval(t1, t2)

    assert iv1.duration_us == 1000000
    assert iv1.duration_seconds() == 1.0
    assert iv1.contains(t0) is True
    assert iv1.contains(t1) is False
    assert iv1.overlaps(iv2) is False
    assert iv1.is_adjacent_to(iv2) is True

    with pytest.raises(ValueError):
        Interval(t1, t0)
    with pytest.raises(ValueError):
        Interval(t1, t1)


def test_tile_check():
    t0 = TimeUs(0)
    t1 = TimeUs(1000000)
    t2 = TimeUs(2000000)

    ivs = [Interval(t0, t1), Interval(t1, t2)]
    assert tile_check(ivs, t2) is True
    assert tile_check([Interval(t0, t1)], t2) is False


def test_snap_to_nearest():
    t0 = TimeUs(0)
    t1 = TimeUs(1000000)
    t5 = TimeUs(5000000)
    target = TimeUs(900000)

    assert snap_to_nearest(target, [t0, t1, t5]) == t1
