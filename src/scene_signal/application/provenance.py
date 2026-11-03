"""Provenance builder with allow-list and redaction guards."""

from typing import Any, Dict, List, Optional
from scene_signal.schemas.result import Provenance


def build_provenance(
    job_id: str,
    asset_id: str,
    asset_fingerprint: str,
    contract_version: str,
    schema_version: str,
    extraction_profile: str,
    request_hash: str,
    sampling_strategy_version: str,
    sampling_parameters: Dict[str, Any],
    media_probe: Dict[str, str],
    frame_extractor: Dict[str, str],
    shot_detector: Dict[str, Any],
    vision: Optional[Dict[str, Any]],
    started_at: str,
    completed_at: str,
    stage_attempts: Dict[str, int],
    warning_count: int,
) -> Provenance:
    """Build Provenance from strictly allowed metadata fields with redaction check."""
    # Redaction guard: ensure no secret keys present in any config
    for d in [sampling_parameters, media_probe, frame_extractor, shot_detector, vision]:
        if d:
            for k in d.keys():
                if any(sec in k.lower() for sec in ["api_key", "token", "secret", "password", "auth"]):
                    raise ValueError(f"Secret-like key '{k}' found in provenance metadata")

    return Provenance(
        job_id=job_id,
        asset_id=asset_id,
        asset_fingerprint=asset_fingerprint,
        contract_version=contract_version,
        schema_version=schema_version,
        extraction_profile=extraction_profile,
        request_hash=request_hash,
        sampling_strategy_version=sampling_strategy_version,
        sampling_parameters=sampling_parameters,
        media_probe=media_probe,
        frame_extractor=frame_extractor,
        shot_detector=shot_detector,
        vision=vision,
        started_at=started_at,
        completed_at=completed_at,
        stage_attempts=stage_attempts,
        warning_count=warning_count,
    )
