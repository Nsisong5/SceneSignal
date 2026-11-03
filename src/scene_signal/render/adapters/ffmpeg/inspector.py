from pathlib import Path
import subprocess
import json
from decimal import Decimal
from fractions import Fraction
from scene_signal.render.ports.media_probe import MediaInspectorPort, SourceMediaInfo, AudioStreamInfo
from scene_signal.render.domain.errors import RenderError
from scene_signal.render.adapters.ffmpeg.binaries import FFmpegBinaries

ALLOWED_CONTAINERS = {"mov", "mp4", "m4a", "3gp", "3g2", "mj2", "matroska", "webm"}

class FfprobeInspector(MediaInspectorPort):
    def inspect(self, path: Path) -> SourceMediaInfo:
        if not path.exists():
            raise RenderError("ASSET_NOT_FOUND", f"Media file not found: {path}", retryable=False, phase="inspect")

        ffprobe_bin = FFmpegBinaries.locate_binary("ffprobe")

        # Security check: if file is text/ffconcat playlist
        try:
            content = path.read_bytes()
            if b"ffconcat" in content or b"file " in content:
                raise RenderError(
                    code="SOURCE_MEDIA_INVALID",
                    message="Unsupported container (playlist/ffconcat trap)",
                    retryable=False,
                    phase="inspect",
                    details={"reason": "unsupported_container"},
                )
        except RenderError:
            raise
        except Exception:
            pass

        cmd = [
            ffprobe_bin,
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
            stderr = e.stderr.lower()
            reason = "corrupt"
            if "not found" in stderr or "invalid data" in stderr:
                reason = "corrupt"
            raise RenderError(
                code="SOURCE_MEDIA_INVALID",
                message=f"ffprobe failed to inspect media: {e.stderr[:500]}",
                retryable=False,
                phase="inspect",
                details={"reason": reason, "stderr": e.stderr[:500]},
            ) from e
        except Exception as e:
            raise RenderError(
                code="SOURCE_MEDIA_INVALID",
                message=f"ffprobe execution error: {e}",
                retryable=False,
                phase="inspect",
                details={"reason": "corrupt"},
            ) from e

        try:
            data = json.loads(res.stdout)
        except Exception as e:
            raise RenderError(
                code="SOURCE_MEDIA_INVALID",
                message="Failed to parse ffprobe JSON output",
                retryable=False,
                phase="inspect",
                details={"reason": "corrupt"},
            ) from e

        format_info = data.get("format", {})
        streams = data.get("streams", [])

        format_name = format_info.get("format_name", "").lower()
        if not any(c in format_name for c in ALLOWED_CONTAINERS):
            raise RenderError(
                code="SOURCE_MEDIA_INVALID",
                message=f"Unsupported container format: {format_name}",
                retryable=False,
                phase="inspect",
                details={"reason": "unsupported_container"},
            )

        video_streams = [s for s in streams if s.get("codec_type") == "video" and not s.get("disposition", {}).get("attached_pic", 0)]
        audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

        if not video_streams:
            if any(s.get("codec_type") == "audio" for s in streams):
                raise RenderError(
                    code="SOURCE_MEDIA_INVALID",
                    message="Audio-only media file rejected",
                    retryable=False,
                    phase="inspect",
                    details={"reason": "no_video_stream"},
                )
            raise RenderError(
                code="SOURCE_MEDIA_INVALID",
                message="No valid video stream found (possibly still image)",
                retryable=False,
                phase="inspect",
                details={"reason": "not_video"},
            )

        video_stream = video_streams[0]
        
        # Check if still image (duration infinite or 1 frame)
        if video_stream.get("nb_frames") == "1" or format_info.get("duration") is None:
            raise RenderError(
                code="SOURCE_MEDIA_INVALID",
                message="Still image rejected",
                retryable=False,
                phase="inspect",
                details={"reason": "not_video"},
            )

        duration = Decimal(str(format_info.get("duration", video_stream.get("duration", "0"))))
        start_time = Decimal(str(format_info.get("start_time", video_stream.get("start_time", "0"))))

        width = int(video_stream.get("width", 1280))
        height = int(video_stream.get("height", 720))
        sar = video_stream.get("sample_aspect_ratio", "1:1")
        if sar == "0:1" or not sar:
            sar = "1:1"

        rotation = 0
        side_data = video_stream.get("side_data_list", [])
        for sd in side_data:
            if "rotation" in sd:
                rotation = int(sd["rotation"])
        if rotation == 0:
            tags = video_stream.get("tags", {})
            if "rotate" in tags:
                rotation = int(tags["rotate"])
        rotation = rotation % 360

        fps_str = video_stream.get("r_frame_rate", "30/1")
        try:
            if "/" in fps_str:
                num, den = fps_str.split("/")
                fps = Fraction(int(num), int(den))
            else:
                fps = Fraction(int(float(fps_str)), 1)
        except Exception:
            fps = Fraction(30, 1)

        is_vfr = video_stream.get("avg_frame_rate") != video_stream.get("r_frame_rate")
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
            start_time_seconds=start_time,
            width=width,
            height=height,
            sar=sar,
            rotation=rotation,
            frame_rate=fps,
            is_vfr=is_vfr,
            has_video=True,
            has_audio=audio_stream is not None,
            audio=audio_info,
            container_format=format_name,
            video_codec=video_codec,
            stream_count=len(streams),
        )
