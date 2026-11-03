"""Fake shot detection adapter for testing."""

from pathlib import Path
from typing import Optional
from scene_signal.ports.shot_detection import ShotDetectionResult, ShotDetectionPort


class FakeShotDetectionAdapter(ShotDetectionPort):
    def __init__(self, result: Optional[ShotDetectionResult] = None, fail_with: Optional[Exception] = None):
        self.result = result or ShotDetectionResult()
        self.fail_with = fail_with

    def detect(self, media_path: Path, threshold: float = 0.30) -> ShotDetectionResult:
        if self.fail_with:
            raise self.fail_with
        return self.result
