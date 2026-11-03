"""Unit tests for IdAllocator."""

from scene_signal.domain.ids import IdAllocator


def test_id_allocator():
    alloc = IdAllocator("shot")
    assert alloc.next_id() == "shot-001"
    assert alloc.next_id() == "shot-002"

    # Simulate widening past 999
    alloc._counter = 998
    assert alloc.next_id() == "shot-999"
    assert alloc.next_id() == "shot-1000"
    assert alloc.next_id() == "shot-1001"

    alloc.reset()
    assert alloc.next_id() == "shot-001"
