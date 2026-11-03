"""Unit tests for FakeMediaProbe."""

from pathlib import Path
import pytest
from scene_signal.adapters.fakes.fake_media_probe import FakeMediaProbe
from scene_signal.ports.media_probe import MediaInspection


def test_fake_media_probe_default():
    probe = FakeMediaProbe()
    inspection = probe.inspect(Path("dummy.mp4"))
    assert inspection.duration_seconds == 5.0
    assert inspection.width == 1280
    assert inspection.has_video is True


def test_fake_media_probe_custom():
    probe = FakeMediaProbe()
    custom = MediaInspection(
        duration_seconds=10.0,
        container_duration_seconds=10.0,
        width=1920,
        height=1080,
        display_width=1920,
        display_height=1080,
        rotation_degrees=0,
        pixel_aspect_ratio="1:1",
        has_video=True,
        has_audio=True,
        frame_rate=30.0,
        frame_rate_mode="constant",
        frame_count=300,
        video_codec="h264",
        audio_codec="aac",
        container_format="mp4",
        video_time_base="1/15360",
        file_size_bytes=500000,
    )
    p = Path("custom.mp4")
    probe.set_inspection(p, custom)
    assert probe.inspect(p).duration_seconds == 10.0
