from pathlib import Path
from decimal import Decimal
from fractions import Fraction
from scene_signal.render.ports.media_probe import MediaInspectorPort, SourceMediaInfo, AudioStreamInfo

class FakeMediaInspector(MediaInspectorPort):
    def __init__(self, default_width: int = 1280, default_height: int = 720, default_fps: Fraction = Fraction(30, 1), default_duration: Decimal = Decimal("4.0")) -> None:
        self.default_width = default_width
        self.default_height = default_height
        self.default_fps = default_fps
        self.default_duration = default_duration

    def inspect(self, path: Path) -> SourceMediaInfo:
        # If it's a real file rendered by fake engine or ffprobe, return matching info
        content = path.read_bytes() if path.exists() else b""
        if content == b"fake rendered mp4 content":
            return SourceMediaInfo(
                path=str(path),
                duration_seconds=self.default_duration,
                start_time_seconds=Decimal("0.0"),
                width=self.default_width,
                height=self.default_height,
                sar="1:1",
                rotation=0,
                frame_rate=self.default_fps,
                is_vfr=False,
                has_video=True,
                has_audio=False,
                container_format="mov,mp4",
                video_codec="h264",
                stream_count=1,
            )
        
        return SourceMediaInfo(
            path=str(path),
            duration_seconds=Decimal("10.0"),
            start_time_seconds=Decimal("0.0"),
            width=640,
            height=360,
            sar="1:1",
            rotation=0,
            frame_rate=Fraction(24, 1),
            is_vfr=False,
            has_video=True,
            has_audio=False,
            container_format="mov,mp4",
            video_codec="h264",
            stream_count=1,
        )
