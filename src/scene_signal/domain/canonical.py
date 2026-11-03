"""Canonical JSON serialization and request hashing (D-03)."""

import hashlib
import json
from typing import Any

from scene_signal.schemas.job import ExtractionJob


def canonical_json(obj: Any) -> bytes:
    """Produce deterministic canonical JSON bytes with sorted keys."""
    if hasattr(obj, "model_dump"):
        data = obj.model_dump(mode="json", exclude={"correlation_id"})
    elif isinstance(obj, dict):
        data = dict(obj)
        data.pop("correlation_id", None)
    else:
        data = obj

    return json.dumps(
        data,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def request_hash(job: ExtractionJob) -> str:
    """Compute sha256 request hash excluding correlation_id (D-03)."""
    raw = canonical_json(job)
    digest = hashlib.sha256(raw).hexdigest()
    return f"sha256:{digest}"
