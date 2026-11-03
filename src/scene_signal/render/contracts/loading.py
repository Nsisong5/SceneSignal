import json
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

MAX_JSON_SIZE_BYTES = 1 * 1024 * 1024  # 1 MiB

class DuplicateKeyError(ValueError):
    pass

class StrictDecoder(json.JSONDecoder):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        def object_pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            result = {}
            for k, v in pairs:
                if k in result:
                    raise DuplicateKeyError(f"Duplicate key found in JSON object: {k}")
                result[k] = v
            return result

        kwargs['object_pairs_hook'] = object_pairs_hook
        kwargs['parse_float'] = parse_float_strict
        kwargs['parse_constant'] = parse_constant_strict
        super().__init__(*args, **kwargs)

def parse_constant_strict(val: str) -> Any:
    raise ValueError(f"Invalid numeric constant (NaN/Infinity not allowed): {val}")

def parse_float_strict(val: str) -> Decimal:
    if val in ("NaN", "Infinity", "-Infinity", "inf", "-inf"):
        raise ValueError(f"Float constants (NaN/Infinity) are not allowed: {val}")

    try:
        d = Decimal(val)
    except Exception as e:
        raise ValueError(f"Invalid float representation: {val}") from e

    # Check decimal places <= 6
    # To check precision correctly on the microsecond grid
    # Quantize to 6 decimal places
    quantized = d.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
    diff = abs(d - quantized)

    if diff <= Decimal("1e-9"):
        return quantized
    else:
        # Check if it has more than 6 decimal places without snapping if diff > 1e-9
        # Actually K-10 states: "floats within 1e-9 of the grid are snapped, others rejected."
        raise ValueError(f"Float value {val} exceeds 6 decimal places precision (diff {diff} > 1e-9)")

def load_strict_json(content: str | bytes) -> Any:
    if isinstance(content, bytes):
        if len(content) > MAX_JSON_SIZE_BYTES:
            raise ValueError(f"JSON payload exceeds size limit of 1 MiB: {len(content)} bytes")
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as e:
            raise ValueError("JSON payload is not valid UTF-8") from e
    else:
        if len(content.encode("utf-8")) > MAX_JSON_SIZE_BYTES:
            raise ValueError("JSON payload exceeds size limit of 1 MiB")
        text = content

    # Check for trailing garbage using raw_decode
    decoder = StrictDecoder()
    try:
        idx = 0
        while idx < len(text) and text[idx].isspace():
            idx += 1
        if idx >= len(text):
            raise ValueError("Empty JSON document")

        obj, end_idx = decoder.raw_decode(text, idx)

        while end_idx < len(text) and text[end_idx].isspace():
            end_idx += 1
        if end_idx < len(text):
            raise ValueError("Trailing data after valid JSON document")
        return obj
    except (json.JSONDecodeError, DuplicateKeyError) as e:
        raise ValueError(f"Invalid JSON: {e}") from e
