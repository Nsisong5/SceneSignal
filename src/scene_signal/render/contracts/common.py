import re
from fractions import Fraction
from typing import Annotated, Any

from pydantic import AfterValidator, PlainSerializer, WithJsonSchema

ID_REGEX = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
CHECKSUM_REGEX = re.compile(r"^sha256:[0-9a-f]{64}$")

def validate_id(v: str) -> str:
    if not isinstance(v, str) or not ID_REGEX.match(v):
        raise ValueError(f"Invalid ID format: {v}")
    return v

def validate_checksum(v: str | None) -> str | None:
    if v is None:
        return None
    if not isinstance(v, str) or not CHECKSUM_REGEX.match(v):
        raise ValueError(f"Invalid checksum format: {v}")
    return v

def parse_fps(v: Any) -> Fraction:
    if isinstance(v, bool):
        raise ValueError("Boolean is not a valid FPS")
    if isinstance(v, int):
        if v <= 0:
            raise ValueError(f"FPS must be positive: {v}")
        return Fraction(v, 1)
    if isinstance(v, str):
        v = v.strip()
        try:
            if "/" in v:
                parts = v.split("/")
                if len(parts) != 2:
                    raise ValueError
                num = int(parts[0])
                den = int(parts[1])
                if num <= 0 or den <= 0:
                    raise ValueError
                return Fraction(num, den)
            else:
                val = int(v)
                if val <= 0:
                    raise ValueError
                return Fraction(val, 1)
        except Exception as e:
            raise ValueError(f"Invalid FPS string format: {v}") from e
    if isinstance(v, Fraction):
        return v
    raise ValueError(f"Invalid FPS type: {type(v)}")

def serialize_fps(fps: Fraction) -> str | int:
    if fps.denominator == 1:
        return fps.numerator
    return f"{fps.numerator}/{fps.denominator}"

Fps = Annotated[
    Fraction,
    AfterValidator(parse_fps),
    PlainSerializer(serialize_fps, return_type=str | int),
    WithJsonSchema({"type": ["string", "integer"], "description": "Exact rational frame rate (e.g. 30 or 30000/1001)"}),
]

PlanId = Annotated[str, AfterValidator(validate_id)]
SegmentId = Annotated[str, AfterValidator(validate_id)]
AssetId = Annotated[str, AfterValidator(validate_id)]
TransitionId = Annotated[str, AfterValidator(validate_id)]
RenderJobId = Annotated[str, AfterValidator(validate_id)]
ProductionId = Annotated[str, AfterValidator(validate_id)]
CorrelationId = Annotated[str, AfterValidator(validate_id)]
Checksum = Annotated[str | None, AfterValidator(validate_checksum)]
