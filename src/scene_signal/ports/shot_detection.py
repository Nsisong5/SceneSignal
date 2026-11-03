"""Shot detection port definitions."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class BoundaryCandidate:
    time_us: int
    kind: str  # "hard_cut" | "black_gap_start" | "black_gap_end"
    score: Optional[float] = None
    score_meaning: Optional[str] = None
    uncertainty_us: Optional[int] = None


@dataclass(frozen=True)
class BlackInterval:
    start_us: int
    end_us: int


@dataclass(frozen=True)
class ShotDetectionResult:
    boundaries: List[BoundaryCandidate] = field(default_factory=list)
    black_intervals: List[BlackInterval] = field(default_factory=list)
    method_name: str = "ffmpeg_scene"
    method_version: str = "1.0"
    parameters: dict = field(default_factory=dict)
    limitations: List[str] = field(
        default_factory=lambda: ["hard cuts and black gaps only; gradual transitions not detected."]
    )


class ShotDetectionPort(ABC):
    @abstractmethod
    def detect(self, media_path: Path, threshold: float = 0.30) -> ShotDetectionResult:
        """Detect shot boundaries and black intervals in media."""
        pass
