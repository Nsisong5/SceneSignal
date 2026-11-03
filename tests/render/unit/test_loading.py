import pytest

from scene_signal.render.contracts.loading import load_strict_json


def test_load_valid_json():
    data = load_strict_json('{"a": 1, "b": "test"}')
    assert data == {"a": 1, "b": "test"}

def test_load_reject_nan_infinity():
    with pytest.raises(ValueError):
        load_strict_json('{"a": NaN}')
    with pytest.raises(ValueError):
        load_strict_json('{"a": Infinity}')
    with pytest.raises(ValueError):
        load_strict_json('{"a": -Infinity}')

def test_load_reject_duplicate_keys():
    with pytest.raises(ValueError):
        load_strict_json('{"a": 1, "a": 2}')

def test_load_reject_trailing_data():
    with pytest.raises(ValueError):
        load_strict_json('{"a": 1} {"b": 2}')

def test_load_size_limit():
    huge_json = '{"a": "' + "x" * (2 * 1024 * 1024) + '"}'
    with pytest.raises(ValueError):
        load_strict_json(huge_json)

def test_load_float_precision_and_snapping():
    # Within 1e-9 of grid should snap
    d = load_strict_json('{"val": 1.0000000001}')
    assert "val" in d

    # Outside 1e-9 of grid should be rejected
    with pytest.raises(ValueError):
        load_strict_json('{"val": 1.1234567}')
