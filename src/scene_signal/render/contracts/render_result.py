from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from scene_signal.render.contracts.common import Checksum, PlanId, RenderJobId
from scene_signal.render.contracts.error_info import ErrorInfo


class ArtifactRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    scheme: str = "file"
    uri: str
    checksum: Checksum = None

class OutputMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    ref: ArtifactRef
    container: str
    video_codec: str
    audio_codec: str | None = None
    duration_seconds: Decimal
    width: int
    height: int
    frame_rate: str
    frame_count: int
    has_video: bool
    has_audio: bool
    file_size_bytes: int

class ExpectedMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    duration_seconds: Decimal
    duration_fraction: str
    frame_count: int

class TimingMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    started_at: str
    completed_at: str
    elapsed_seconds: Decimal

class RendererMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    name: str
    version: str
    ffmpeg_version: str
    ffprobe_version: str
    encoder_settings: dict[str, Any]

class PostconditionCheck(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    check: str
    status: Literal["passed", "failed", "skipped"]
    detail: str

class WarningItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    code: str
    message: str
    phase: str
    related_ids: list[str] = []

class RenderResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    contract_version: Literal["1.0"] = "1.0"
    render_job_id: RenderJobId
    plan_id: PlanId
    status: Literal["succeeded", "failed", "cancelled"]
    output: OutputMetadata | None = None
    expected: ExpectedMetadata
    timing: TimingMetadata
    renderer: RendererMetadata
    postconditions: list[PostconditionCheck] = []
    warnings: list[WarningItem] = []
    manifest_ref: ArtifactRef
    error: ErrorInfo | None = None
