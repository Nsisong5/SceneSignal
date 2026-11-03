"""Frame extraction port and data structures."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class FrameRequest:
    planned_time_us: int


@dataclass(frozen=True)
class ExtractedFrame:
    path: Path
    requested_us: int
    actual_us: int
    pts: Optional[int]
    time_base: Optional[str]
    frame_index: Optional[int]
    width: int
    height: int
    timestamp_source: str  # "decoded_pts" | "requested_unverified"
    warnings: List[str] = field(default_factory=list)


class FrameExtractionPort(ABC):
    @abstractmethod
    def extract(
        self,
        media_path: Path,
        requests: List[FrameRequest],
        out_dir: Path,
        max_long_edge: int = 1024,
    ) -> List[ExtractedFrame]:
        """Extract still frames at requested timestamps from media."""
        pass
