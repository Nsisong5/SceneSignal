from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from scene_signal.render.contracts.common import (
    AssetId,
    Checksum,
    Fps,
    PlanId,
    ProductionId,
    SegmentId,
    TransitionId,
)


class AssetRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    scheme: str = "file"
    uri: str
    checksum: Checksum = None

class PlanAsset(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    asset_id: AssetId
    asset_ref: AssetRef

class AudioProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    codec: str = "aac"
    sample_rate: int = 48000
    channels: int = 2

class OutputProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    name: str | None = Field(default=None, max_length=64)
    container: Literal["mp4"] = "mp4"
    video_codec: Literal["h264"] = "h264"
    width: int
    height: int
    fps: Fps
    fit: Literal["letterbox", "crop"]
    audio: AudioProfile | None = None

class Segment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    segment_id: SegmentId
    asset_id: AssetId
    source_start_seconds: Decimal
    source_end_seconds: Decimal
    audio_mode: Literal["source", "mute"]

class Transition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    transition_id: TransitionId
    type: str
    from_segment_id: SegmentId
    to_segment_id: SegmentId
    duration_seconds: Decimal

class Timeline(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    segments: list[Segment] = Field(default_factory=list, min_length=1)
    transitions: list[Transition] = Field(default_factory=list)

class EditPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    contract_version: Literal["1.0"] = "1.0"
    plan_id: PlanId
    production_id: ProductionId | None = None
    assets: list[PlanAsset] = Field(default_factory=list, min_length=1)
    output_profile: OutputProfile
    timeline: Timeline
    expected_duration_seconds: Decimal | None = None
