from pathlib import Path
import subprocess
import json
from decimal import Decimal
from fractions import Fraction
from scene_signal.render.ports.media_probe import MediaInspectorPort, SourceMediaInfo, AudioStreamInfo
from scene_signal.render.domain.errors import RenderError

class FFmpegMediaInspector(MediaInspectorPort):
    def inspect(self, path: Path) -> SourceMediaInfo:
        if not path.exists():
            raise RenderError("ASSET_NOT_FOUND", f"Media file not found: {path}", retryable=False, phase="inspect")

        cmd = [
            "ffprobe",
            "-v", "error",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(path),
        ]

        try:
            res = subprocess.run(
                cmd,
                shell=False,
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.CalledProcessError as e:
            raise RenderError(
                code="SOURCE_MEDIA_INVALID",
                message=f"ffprobe failed to inspect media: {e.stderr[:500]}",
                retryable=False,
                phase="inspect",
                details={"stderr": e.stderr[:500]}
            ) from e
        except Exception as e:
            raise RenderError(
                code="SOURCE_MEDIA_INVALID",
                message=f"ffprobe execution error: {e}",
                retryable=False,
                phase="inspect",
            ) from e

        try:
            data = json.loads(res.stdout)
        except Exception as e:
            raise RenderError(
                code="SOURCE_MEDIA_INVALID",
                message="Failed to parse ffprobe JSON output",
                retryable=False,
                phase="inspect",
            ) from e

        format_info = data.get("format", {})
        streams = data.get("streams", [])

        duration = Decimal(str(format_info.get("duration", "0")))
        container_format = format_info.get("format_name", "mov,mp4")

        video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
        audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

        if not video_stream:
            raise RenderError(
                code="SOURCE_MEDIA_INVALID",
                message="No video stream found in media file",
                retryable=False,
                phase="inspect",
            )

        width = int(video_stream.get("width", 1280))
        height = int(video_stream.get("height", 720))
        sar = video_stream.get("sample_aspect_ratio", "1:1")
        if sar == "0:1" or not sar:
            sar = "1:1"

        # Rotation from side_data_list or tags
        rotation = 0
        side_data = video_stream.get("side_data_list", [])
        for sd in side_data:
            if "rotation" in sd:
                rotation = int(sd["rotation"])
        if rotation == 0:
            tags = video_stream.get("tags", {})
            if "rotate" in tags:
                rotation = int(tags["rotate"])

        # Frame rate
        fps_str = video_stream.get("r_frame_rate", "30/1")
        try:
            if "/" in fps_str:
                num, den = fps_str.split("/")
                fps = Fraction(int(num), int(den))
            else:
                fps = Fraction(int(float(fps_str)), 1)
        except Exception:
            fps = Fraction(30, 1)

        is_vfr = False # simplified
        video_codec = video_stream.get("codec_name", "h264")

        audio_info = None
        if audio_stream:
            a_codec = audio_stream.get("codec_name", "aac")
            sample_rate = int(audio_stream.get("sample_rate", 48000))
            channels = int(audio_stream.get("channels", 2))
            audio_info = AudioStreamInfo(codec=a_codec, sample_rate=sample_rate, channels=channels)

        return SourceMediaInfo(
            path=str(path),
            duration_seconds=duration,
            start_time_seconds=Decimal(str(format_info.get("start_time", "0"))),
            width=width,
            height=height,
            sar=sar,
            rotation=rotation,
            frame_rate=fps,
            is_vfr=is_vfr,
            has_video=True,
            has_audio=audio_stream is not None,
            audio=audio_info,
            container_format=container_format,
            video_codec=video_codec,
            stream_count=len(streams),
        )
