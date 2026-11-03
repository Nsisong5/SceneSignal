"""Visual analysis port definitions and error classes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from scene_signal.domain.errors import ErrorCode, ExtractionError


class ProviderTimeout(ExtractionError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code=ErrorCode.PROVIDER_TIMEOUT,
            message=message,
            retryable=True,
            stage="analyze",
            details=details,
        )


class ProviderRateLimited(ExtractionError):
    def __init__(self, message: str, retry_after_seconds: Optional[float] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code=ErrorCode.PROVIDER_RATE_LIMITED,
            message=message,
            retryable=True,
            stage="analyze",
            details=details,
            retry_after_seconds=retry_after_seconds,
        )


class ProviderUnavailable(ExtractionError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code=ErrorCode.PROVIDER_UNAVAILABLE,
            message=message,
            retryable=True,
            stage="analyze",
            details=details,
        )


class ProviderResponseInvalid(ExtractionError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code=ErrorCode.PROVIDER_RESPONSE_INVALID,
            message=message,
            retryable=False,
            stage="analyze",
            details=details,
        )


class ProviderConfigurationError(ExtractionError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code=ErrorCode.PROVIDER_CONFIGURATION_ERROR,
            message=message,
            retryable=False,
            stage="analyze",
            details=details,
        )


class VisionMode(str, Enum):
    STILL_FRAMES = "still_frames"
    FRAME_SEQUENCE = "frame_sequence"
    VIDEO_CLIP = "video_clip"
    DETERMINISTIC = "deterministic"


@dataclass(frozen=True)
class VisionCapabilities:
    provider: str
    model: str
    adapter_version: str
    analysis_mode: VisionMode
    supported_capabilities: List[str]
    supports_temporal_intervals: bool = False
    max_frames_per_call: int = 16


@dataclass(frozen=True)
class VisionAnalysisRequest:
    job_id: str
    shot_id: str
    shot_start_seconds: float
    shot_end_seconds: float
    frame_paths: List[Path]
    frame_timestamps_seconds: List[float]
    requested_capabilities: List[str]
    context_hints: Optional[dict] = None


@dataclass(frozen=True)
class RawObservation:
    id: str
    category: str
    scope: str
    timestamp_seconds: Optional[float] = None
    start_seconds: Optional[float] = None
    end_seconds: Optional[float] = None
    description: str = ""
    value: Optional[str] = None
    entity_refs: List[str] = field(default_factory=list)
    evidence_frame_refs: List[str] = field(default_factory=list)
    evidence_type: str = "direct_observation"
    confidence: Optional[float] = None
    confidence_source: Optional[str] = None
    limitations: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class RawEntity:
    id: str
    type: str
    label: str
    attributes: List[str] = field(default_factory=list)
    identity_scope: str = "shot"
    tracking_method: str = "none"
    identity_notes: Optional[str] = None


@dataclass(frozen=True)
class RawEvent:
    id: str
    type: str
    description: str
    entity_refs: List[str] = field(default_factory=list)
    evidence_observation_refs: List[str] = field(default_factory=list)
    first_seconds: float = 0.0
    last_seconds: float = 0.0
    start_seconds: Optional[float] = None
    end_seconds: Optional[float] = None
    temporal_precision: str = "single_sample_only"
    evidence_type: str = "inference"
    confidence: Optional[float] = None
    confidence_source: Optional[str] = None
    limitations: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class VisionAnalysisResponse:
    shot_summary: Optional[str] = None
    observations: List[RawObservation] = field(default_factory=list)
    entities: List[RawEntity] = field(default_factory=list)
    events: List[RawEvent] = field(default_factory=list)
    raw_payload: Optional[dict] = None


class VisualAnalysisPort(ABC):
    @abstractmethod
    def capabilities(self) -> VisionCapabilities:
        pass

    @abstractmethod
    def analyze(self, request: VisionAnalysisRequest) -> VisionAnalysisResponse:
        pass
