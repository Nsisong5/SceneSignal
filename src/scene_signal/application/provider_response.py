"""Provider response negotiation and untrusted data validation."""

from dataclasses import dataclass, field
from typing import List, Optional
from scene_signal.ports.visual_analysis import (
    ProviderResponseInvalid,
    VisionAnalysisRequest,
    VisionAnalysisResponse,
    VisionCapabilities,
    RawObservation,
    RawEntity,
    RawEvent,
)


@dataclass(frozen=True)
class CapabilityNegotiation:
    capability: str
    requested: bool
    status: str  # "completed" | "partial" | "unsupported" | "not_requested"
    analysis_mode: Optional[str] = None
    limitations: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class NegotiationResult:
    reports: List[CapabilityNegotiation]


def negotiate(
    requested_capabilities: List[str],
    caps: VisionCapabilities,
    available_mode: str,
) -> NegotiationResult:
    """Negotiate capabilities between request and provider capabilities."""
    all_known = {"shot_detection", "visual_observations", "temporal_events", "camera_analysis", "visible_text"}
    reports: List[CapabilityNegotiation] = []

    for cap in all_known:
        requested = cap in requested_capabilities
        if not requested:
            reports.append(
                CapabilityNegotiation(
                    capability=cap,
                    requested=False,
                    status="not_requested",
                )
            )
            continue

        if cap in caps.supported_capabilities:
            reports.append(
                CapabilityNegotiation(
                    capability=cap,
                    requested=True,
                    status="completed",
                    analysis_mode=available_mode,
                )
            )
        else:
            reports.append(
                CapabilityNegotiation(
                    capability=cap,
                    requested=True,
                    status="unsupported",
                    analysis_mode=None,
                    limitations=[f"Provider '{caps.provider}' does not support capability '{cap}'."],
                )
            )

    return NegotiationResult(reports=reports)


@dataclass(frozen=True)
class ValidatedResponse:
    shot_summary: Optional[str]
    observations: List[RawObservation]
    entities: List[RawEntity]
    events: List[RawEvent]
    warnings: List[str]


def validate_response(
    request: VisionAnalysisRequest,
    response: VisionAnalysisResponse,
    caps: VisionCapabilities,
) -> ValidatedResponse:
    """Validate untrusted provider response data against request and capabilities."""
    warnings: List[str] = []
    valid_categories = {
        "object_presence",
        "action",
        "environment",
        "composition",
        "lighting",
        "style",
        "shot_size",
        "camera_angle",
        "camera_movement",
        "subject_movement",
        "visible_text",
        "visual_transition",
        "other",
    }

    valid_frame_refs = {f"frame-{i+1:03d}" for i in range(len(request.frame_paths))}

    valid_obs: List[RawObservation] = []
    for obs in response.observations:
        if not obs.description or not obs.description.strip():
            continue
        if obs.category not in valid_categories:
            warnings.append("PROVIDER_ITEM_DROPPED")
            continue

        for ref in obs.evidence_frame_refs:
            if ref not in valid_frame_refs:
                raise ProviderResponseInvalid(f"Unknown frame reference: {ref}")

        conf = obs.confidence
        if conf is not None and (conf < 0.0 or conf > 1.0):
            obs = RawObservation(
                id=obs.id,
                category=obs.category,
                scope=obs.scope,
                timestamp_seconds=obs.timestamp_seconds,
                start_seconds=obs.start_seconds,
                end_seconds=obs.end_seconds,
                description=obs.description,
                value=obs.value,
                entity_refs=obs.entity_refs,
                evidence_frame_refs=obs.evidence_frame_refs,
                evidence_type=obs.evidence_type,
                confidence=None,
                confidence_source=None,
                limitations=obs.limitations,
            )

        valid_obs.append(obs)

    return ValidatedResponse(
        shot_summary=response.shot_summary,
        observations=valid_obs,
        entities=response.entities,
        events=response.events,
        warnings=warnings,
    )
