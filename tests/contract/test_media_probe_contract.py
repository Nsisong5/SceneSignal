"""Contract tests for MediaProbePort adapters (Fake and FFprobe)."""

from pathlib import Path
import pytest
from scene_signal.adapters.fakes.fake_media_probe import FakeMediaProbe
from scene_signal.adapters.media.ffprobe import FFprobeAdapter
from scene_signal.domain.errors import ExtractionError


def test_fake_media_probe_contract():
    probe = FakeMediaProbe()
    res = probe.inspect(Path("any.mp4"))
    assert res.duration_seconds > 0
    assert res.has_video is True


@pytest.mark.requires_ffmpeg
def test_ffprobe_adapter_contract_synthetic():
    adapter = FFprobeAdapter()
    fixture_path = Path("tests/fixtures/media/clip_5s_landscape_audio.mp4")
    if not fixture_path.exists():
        pytest.skip("Synthetic fixture clip_5s_landscape_audio.mp4 not found")

    inspection = adapter.inspect(fixture_path)
    assert inspection.duration_seconds == pytest.approx(5.0, abs=0.2)
    assert inspection.width == 1280
    assert inspection.height == 720
    assert inspection.has_video is True
    assert inspection.has_audio is True
    assert inspection.video_codec == "h264"


@pytest.mark.requires_ffmpeg
def test_ffprobe_adapter_not_found():
    adapter = FFprobeAdapter()
    with pytest.raises(ExtractionError) as exc_info:
        adapter.inspect(Path("non_existent_file_12345.mp4"))
    assert exc_info.value.code.value == "ASSET_NOT_FOUND"


@pytest.mark.requires_ffmpeg
def test_ffprobe_adapter_zero_bytes(tmp_path):
    adapter = FFprobeAdapter()
    zero_file = tmp_path / "zero.mp4"
    zero_file.write_bytes(b"")
    with pytest.raises(ExtractionError) as exc_info:
        adapter.inspect(zero_file)
    assert exc_info.value.code.value == "MEDIA_INVALID_OR_CORRUPT"
