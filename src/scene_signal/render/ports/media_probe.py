from abc import ABC, abstractmethod
from pathlib import Path
from decimal import Decimal
from fractions import Fraction
from pydantic import BaseModel, ConfigDict

class AudioStreamInfo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    codec: str
    sample_rate: int
    channels: int

class SourceMediaInfo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    path: str
    duration_seconds: Decimal
    start_time_seconds: Decimal = Decimal("0")
    width: int
    height: int
    sar: str = "1:1"
    rotation: int = 0
    frame_rate: Fraction
    is_vfr: bool = False
    has_video: bool = True
    has_audio: bool = False
    audio: AudioStreamInfo | None = None
    container_format: str = "mov,mp4,m4a,3gp,3g2,mj2"
    video_codec: str = "h264"
    stream_count: int = 1

class MediaInspectorPort(ABC):
    @abstractmethod
    def inspect(self, path: Path) -> SourceMediaInfo:
        pass
