"""Fake media inspection adapter for testing."""

from pathlib import Path
from typing import Dict, Optional
from scene_signal.ports.media_probe import MediaInspection, MediaProbePort


class FakeMediaProbe(MediaProbePort):
    def __init__(self, default_inspection: Optional[MediaInspection] = None):
        self.default_inspection = default_inspection or MediaInspection(
            duration_seconds=5.0,
            container_duration_seconds=5.0,
            width=1280,
            height=720,
            display_width=1280,
            display_height=720,
            rotation_degrees=0,
            pixel_aspect_ratio="1:1",
            has_video=True,
            has_audio=False,
            frame_rate=24.0,
            frame_rate_mode="constant",
            frame_count=120,
            video_codec="h264",
            audio_codec=None,
            container_format="mp4",
            video_time_base="1/12288",
            file_size_bytes=123456,
        )
        self.path_inspections: Dict[Path, MediaInspection] = {}
        self.errors_to_raise: Dict[Path, Exception] = {}

    def set_inspection(self, path: Path, inspection: MediaInspection) -> None:
        self.path_inspections[path] = inspection

    def set_error(self, path: Path, error: Exception) -> None:
        self.errors_to_raise[path] = error

    def inspect(self, path: Path) -> MediaInspection:
        if path in self.errors_to_raise:
            raise self.errors_to_raise[path]
        return self.path_inspections.get(path, self.default_inspection)
