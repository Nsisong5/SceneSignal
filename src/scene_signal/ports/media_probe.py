"""Media inspection port definition."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class MediaInspection:
    duration_seconds: float
    container_duration_seconds: Optional[float]
    width: int
    height: int
    display_width: int
    display_height: int
    rotation_degrees: int
    pixel_aspect_ratio: Optional[str]
    has_video: bool
    has_audio: bool
    frame_rate: Optional[float]
    frame_rate_mode: str
    frame_count: Optional[int]
    video_codec: str
    audio_codec: Optional[str]
    container_format: str
    video_time_base: Optional[str]
    file_size_bytes: int
    start_time_us: int = 0
    warnings: List[str] = field(default_factory=list)
    probe_name: str = "ffprobe"
    probe_version: str = "6.0"


class MediaProbePort(ABC):
    @abstractmethod
    def inspect(self, path: Path) -> MediaInspection:
        """Inspect media file and return technical metadata."""
        pass
