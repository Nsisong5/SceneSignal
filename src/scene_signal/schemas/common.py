"""Common Pydantic models for SceneSignal contracts."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

ID_REGEX = r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"
CHECKSUM_REGEX = r"^sha256:[0-9a-f]{64}$"
VERSION_REGEX = r"^\d+\.\d+$"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class AssetRef(StrictModel):
    scheme: str = Field(..., min_length=1)
    uri: str = Field(..., min_length=1)
    checksum: Optional[str] = Field(default=None, pattern=CHECKSUM_REGEX)


class ChannelContext(StrictModel):
    channel_id: Optional[str] = Field(default=None, pattern=ID_REGEX)
    style_guidance: Optional[str] = None
    audience: Optional[str] = None
    conventions: List[str] = Field(default_factory=list)


class SourceSegment(StrictModel):
    segment_id: str = Field(..., pattern=ID_REGEX)
    start_seconds: float = Field(..., ge=0.0)
    end_seconds: float = Field(..., ge=0.0)
    order_index: Optional[int] = Field(default=None, ge=0)
    label: Optional[str] = None

    @model_validator(mode="after")
    def validate_interval(self) -> "SourceSegment":
        if self.end_seconds <= self.start_seconds:
            raise ValueError("segment end_seconds must be strictly greater than start_seconds")
        return self


class SourceTimeline(StrictModel):
    segments: List[SourceSegment] = Field(default_factory=list)


class RelatedAsset(StrictModel):
    asset_id: str = Field(..., pattern=ID_REGEX)
    relation: Literal["source_clip", "sibling", "derived_from"]
    asset_ref: Optional[AssetRef] = None


class ErrorInfo(StrictModel):
    code: str
    message: str
    retryable: bool
    stage: str
    attempts: int = Field(..., ge=1)
    details: Dict[str, Any] = Field(default_factory=dict)


class CapabilityReport(StrictModel):
    capability: str
    requested: bool
    status: Literal["completed", "partial", "unsupported", "failed", "not_requested"]
    analysis_mode: Optional[Literal["still_frames", "frame_sequence", "video_clip", "deterministic"]] = None
    limitations: List[str] = Field(default_factory=list)
    error_code: Optional[str] = None


class WarningRecord(StrictModel):
    code: str
    message: str
    stage: str
    severity: Literal["info", "warning"]
    related_ids: List[str] = Field(default_factory=list)
