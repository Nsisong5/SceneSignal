"""Contract tests for frame extraction adapters (Fake and FFmpeg)."""

from pathlib import Path
import pytest
from scene_signal.adapters.fakes.fake_frames import FakeFrameExtractionAdapter
from scene_signal.adapters.media.ffmpeg_frames import FFmpegFrameExtractionAdapter
from scene_signal.ports.frame_extraction import FrameRequest


def test_fake_frame_extraction(tmp_path):
    adapter = FakeFrameExtractionAdapter()
    requests = [FrameRequest(500000), FrameRequest(1500000)]
    out_dir = tmp_path / "frames"
    frames = adapter.extract(Path("dummy.mp4"), requests, out_dir)
    assert len(frames) == 2
    assert frames[0].path.exists()
    assert frames[1].requested_us == 1500000


@pytest.mark.requires_ffmpeg
def test_ffmpeg_frame_extraction_synthetic(tmp_path):
    fixture_path = Path("tests/fixtures/media/clip_5s_landscape_audio.mp4")
    if not fixture_path.exists():
        pytest.skip("Synthetic fixture clip_5s_landscape_audio.mp4 not found")

    adapter = FFmpegFrameExtractionAdapter()
    requests = [FrameRequest(500000), FrameRequest(1500000), FrameRequest(2500000)]
    out_dir = tmp_path / "extracted_frames"
    frames = adapter.extract(fixture_path, requests, out_dir)

    assert len(frames) == 3
    for f in frames:
        assert f.path.exists()
        assert f.path.stat().st_size > 0
        assert f.width > 0
        assert f.height > 0
