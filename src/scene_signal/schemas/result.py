"""SceneIntelligenceDocument, JobResult, and related output schemas."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import Field, field_validator, model_validator

from scene_signal.schemas.common import (
    ID_REGEX,
    VERSION_REGEX,
    CapabilityReport,
    ErrorInfo,
    StrictModel,
    WarningRecord,
)
from scene_signal.schemas.versions import check_schema_version


class MediaMetadata(StrictModel):
    duration_seconds: float = Field(..., gt=0.0)
    container_duration_seconds: Optional[float] = Field(default=None, ge=0.0)
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)
    display_width: int = Field(..., gt=0)
    display_height: int = Field(..., gt=0)
    rotation_degrees: Literal[0, 90, 180, 270]
    pixel_aspect_ratio: Optional[str] = None
    has_video: Literal[True]
    has_audio: bool
    frame_rate: Optional[float] = Field(default=None, gt=0.0)
    frame_rate_mode: Literal["constant", "variable", "unknown"]
    frame_count: Optional[int] = Field(default=None, ge=0)
    video_codec: str
    audio_codec: Optional[str] = None
    container_format: str
    video_time_base: Optional[str] = None
    file_size_bytes: int = Field(..., ge=0)


class TimelineMetadata(StrictModel):
    unit: Literal["seconds"] = "seconds"
    interval_convention: Literal["[start,end)"] = "[start,end)"
    precision_decimals: int = 6
    timeline_kind: Literal["source_media"] = "source_media"
    origin: Literal["first_video_frame"] = "first_video_frame"
    start_time_offset_seconds: float = 0.0
    source_time_base: Optional[str] = None


class Shot(StrictModel):
    id: str = Field(..., pattern=ID_REGEX)
    start_seconds: float = Field(..., ge=0.0)
    end_seconds: float = Field(..., ge=0.0)
    segment_kind: Literal["content", "black"]
    boundary_method: Literal[
        "initial_segment", "whole_asset", "ffmpeg_scene_score", "ffmpeg_blackdetect", "external"
    ]
    boundary_kind: Literal["asset_start", "hard_cut", "black_gap", "none"]
    boundary_score: Optional[float] = None
    boundary_score_meaning: Optional[str] = None
    boundary_uncertainty_seconds: Optional[float] = Field(default=None, ge=0.0)
    frame_ids: List[str] = Field(default_factory=list)
    analysis_status: Literal["analyzed", "failed", "skipped", "not_requested"]
    summary: Optional[str] = None
    observation_ids: List[str] = Field(default_factory=list)
    event_ids: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_interval(self) -> "Shot":
        if self.end_seconds <= self.start_seconds:
            raise ValueError("Shot end_seconds must be strictly greater than start_seconds")
        return self


class FrameRecord(StrictModel):
    id: str = Field(..., pattern=ID_REGEX)
    timestamp_seconds: float = Field(..., ge=0.0)
    requested_timestamp_seconds: float = Field(..., ge=0.0)
    timestamp_source: Literal["decoded_pts", "requested_unverified"]
    pts: Optional[int] = None
    time_base: Optional[str] = None
    frame_index: Optional[int] = Field(default=None, ge=0)
    shot_id: str = Field(..., pattern=ID_REGEX)
    sampling_reason: Literal["shot_bin", "min_total_fill"]
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)
    artifact_ref: Optional[str] = None


class Entity(StrictModel):
    id: str = Field(..., pattern=ID_REGEX)
    type: Literal["person", "animal", "object", "vehicle", "text_element", "place", "other"]
    label: str = Field(..., min_length=1)
    attributes: List[str] = Field(default_factory=list)
    identity_scope: Literal["frame", "shot", "asset"]
    tracking_method: Literal["none", "provider_local_grouping"]
    identity_notes: Optional[str] = None
    shot_ids: List[str] = Field(default_factory=list)
    first_observed_seconds: float = Field(..., ge=0.0)
    last_observed_seconds: float = Field(..., ge=0.0)
    observation_ids: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_observation_interval(self) -> "Entity":
        if self.last_observed_seconds < self.first_observed_seconds:
            raise ValueError("last_observed_seconds cannot be less than first_observed_seconds")
        return self


class Observation(StrictModel):
    id: str = Field(..., pattern=ID_REGEX)
    category: Literal[
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
    ]
    scope: Literal["frame", "shot", "span"]
    timestamp_seconds: Optional[float] = Field(default=None, ge=0.0)
    start_seconds: Optional[float] = Field(default=None, ge=0.0)
    end_seconds: Optional[float] = Field(default=None, ge=0.0)
    shot_id: str = Field(..., pattern=ID_REGEX)
    description: str = Field(..., min_length=1)
    value: Optional[str] = None
    entity_ids: List[str] = Field(default_factory=list)
    evidence_frame_ids: List[str] = Field(default_factory=list)
    evidence_type: Literal["direct_observation", "inference"]
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    confidence_source: Optional[Literal["model_self_reported", "detector_score", "heuristic"]] = None
    limitations: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_scope_and_confidence(self) -> "Observation":
        if self.scope == "frame":
            if self.timestamp_seconds is None:
                raise ValueError("timestamp_seconds is required when scope is frame")
        elif self.scope in ("shot", "span"):
            if self.start_seconds is None or self.end_seconds is None:
                raise ValueError("start_seconds and end_seconds are required when scope is shot or span")
            if self.end_seconds <= self.start_seconds:
                raise ValueError("end_seconds must be strictly greater than start_seconds")

        if self.confidence is not None and self.confidence_source is None:
            raise ValueError("confidence_source is required when confidence is present")
        if self.confidence is None and self.confidence_source is not None:
            raise ValueError("confidence is required when confidence_source is present")
        return self


class EvidenceSpan(StrictModel):
    first_seconds: float = Field(..., ge=0.0)
    last_seconds: float = Field(..., ge=0.0)

    @model_validator(mode="after")
    def validate_span(self) -> "EvidenceSpan":
        if self.last_seconds < self.first_seconds:
            raise ValueError("last_seconds cannot be less than first_seconds")
        return self


class Event(StrictModel):
    id: str = Field(..., pattern=ID_REGEX)
    type: Literal["movement", "interaction", "appearance", "disappearance", "state_change", "transition", "other"]
    description: str = Field(..., min_length=1)
    shot_id: str = Field(..., pattern=ID_REGEX)
    entity_ids: List[str] = Field(default_factory=list)
    evidence_observation_ids: List[str] = Field(default_factory=list)
    evidence_span: EvidenceSpan
    start_seconds: Optional[float] = Field(default=None, ge=0.0)
    end_seconds: Optional[float] = Field(default=None, ge=0.0)
    temporal_precision: Literal["single_sample_only", "multi_sample_span", "adapter_reported_interval", "frame_accurate"]
    evidence_type: Literal["direct_observation", "inference"]
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    confidence_source: Optional[Literal["model_self_reported", "detector_score", "heuristic"]] = None
    limitations: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_precision_rules(self) -> "Event":
        if self.temporal_precision == "single_sample_only":
            if self.evidence_span.first_seconds != self.evidence_span.last_seconds:
                raise ValueError("single_sample_only precision requires first_seconds == last_seconds")
            if self.start_seconds is not None or self.end_seconds is not None:
                raise ValueError("single_sample_only precision cannot have start_seconds or end_seconds set")
        elif self.temporal_precision == "multi_sample_span":
            if self.start_seconds is not None or self.end_seconds is not None:
                raise ValueError("multi_sample_span precision cannot have start_seconds or end_seconds set")
        elif self.temporal_precision in ("adapter_reported_interval", "frame_accurate"):
            if self.start_seconds is None or self.end_seconds is None:
                raise ValueError("adapter_reported_interval and frame_accurate require start_seconds and end_seconds")
            if self.end_seconds <= self.start_seconds:
                raise ValueError("end_seconds must be strictly greater than start_seconds")

        if self.confidence is not None and self.confidence_source is None:
            raise ValueError("confidence_source is required when confidence is present")
        return self


class Provenance(StrictModel):
    job_id: str = Field(..., pattern=ID_REGEX)
    asset_id: str = Field(..., pattern=ID_REGEX)
    asset_fingerprint: str
    contract_version: str = Field(..., pattern=VERSION_REGEX)
    schema_version: str = Field(..., pattern=VERSION_REGEX)
    extraction_profile: Literal["quick", "standard", "thorough"]
    request_hash: str
    sampling_strategy_version: str
    sampling_parameters: Dict[str, Any]
    media_probe: Dict[str, str]
    frame_extractor: Dict[str, str]
    shot_detector: Dict[str, Any]
    vision: Optional[Dict[str, Any]] = None
    started_at: str
    completed_at: str
    stage_attempts: Dict[str, int]
    warning_count: int = Field(..., ge=0)


class SceneIntelligenceDocument(StrictModel):
    schema_version: str = Field(..., pattern=VERSION_REGEX)
    outcome: Literal["complete", "partial"]
    job: Dict[str, Any]
    asset_fingerprint: Optional[str] = None
    checksum_status: Literal["verified", "not_supplied"]
    media: MediaMetadata
    timeline: TimelineMetadata
    capabilities: List[CapabilityReport] = Field(default_factory=list)
    shots: List[Shot] = Field(default_factory=list)
    frames: List[FrameRecord] = Field(default_factory=list)
    entities: List[Entity] = Field(default_factory=list)
    observations: List[Observation] = Field(default_factory=list)
    events: List[Event] = Field(default_factory=list)
    provenance: Provenance
    warnings: List[WarningRecord] = Field(default_factory=list)

    @field_validator("schema_version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        check_schema_version(v)
        return v


class JobResult(StrictModel):
    job_id: str = Field(..., pattern=ID_REGEX)
    status: Literal["succeeded", "partial", "failed"]
    document: Optional[SceneIntelligenceDocument] = None
    error: Optional[ErrorInfo] = None

    @model_validator(mode="after")
    def validate_result_state(self) -> "JobResult":
        if self.status in ("succeeded", "partial") and self.document is None:
            raise ValueError("document is required when status is succeeded or partial")
        if self.status == "failed" and self.error is None:
            raise ValueError("error is required when status is failed")
        return self


class JobStatusRecord(StrictModel):
    job_id: str = Field(..., pattern=ID_REGEX)
    request_hash: str
    status: Literal["pending", "running", "succeeded", "partial", "failed"]
    current_stage: str
    attempt: int = Field(..., ge=1)
    created_at: str
    updated_at: str
    error: Optional[ErrorInfo] = None
