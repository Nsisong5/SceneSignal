import hashlib
import json
from decimal import Decimal
from fractions import Fraction
from typing import Any


def default_canonical(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        # Format decimal without scientific notation if possible, normalized
        return format(obj.normalize(), 'f') if obj == obj.quantize(Decimal('1')) or obj.is_finite() else str(obj)
    if isinstance(obj, Fraction):
        if obj.denominator == 1:
            return obj.numerator
        return f"{obj.numerator}/{obj.denominator}"
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable in canonical form")

def canonical_json(data: Any) -> bytes:
    # Recursively sort keys, compact separators, deterministic float/decimal/fraction
    # Pydantic models can be dumped to dict first
    if hasattr(data, "model_dump"):
        data = data.model_dump(mode="json")

    # We can serialize using standard json dumps with sort_keys=True, separators=(',', ':')
    # Custom encoder handles Decimal and Fraction if needed, or we pre-convert
    def prepare(item: Any) -> Any:
        if isinstance(item, dict):
            return {str(k): prepare(v) for k, v in sorted(item.items())}
        elif isinstance(item, list):
            return [prepare(x) for x in item]
        elif isinstance(item, Decimal):
            # Normalize decimal string representation
            norm = item.normalize()
            # If it has exponent < 0 or > 0, format standard
            s = f"{norm:f}"
            if '.' in s:
                s = s.rstrip('0').rstrip('.')
            return s
        elif isinstance(item, Fraction):
            if item.denominator == 1:
                return item.numerator
            return f"{item.numerator}/{item.denominator}"
        elif isinstance(item, float):
            # Convert float to Decimal first if needed or string
            d = Decimal(str(item))
            norm = d.normalize()
            s = f"{norm:f}"
            if '.' in s:
                s = s.rstrip('0').rstrip('.')
            return s
        return item

    prepared = prepare(data)
    text = json.dumps(prepared, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return text.encode("utf-8")

def plan_fingerprint(plan_data: Any) -> str:
    b = canonical_json(plan_data)
    return f"sha256:{hashlib.sha256(b).hexdigest()}"

def request_hash(request_data: Any) -> str:
    if hasattr(request_data, "model_dump"):
        d = request_data.model_dump(mode="json")
    else:
        d = dict(request_data)
    if "correlation_id" in d:
        d = d.copy()
        d["correlation_id"] = None
    b = canonical_json(d)
    return f"sha256:{hashlib.sha256(b).hexdigest()}"
