"""FFprobe media inspection adapter."""

import json
import shutil
import subprocess
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List

from scene_signal.domain.errors import (
    ErrorCode,
    ExtractionError,
)
from scene_signal.ports.media_probe import MediaInspection, MediaProbePort


class FFprobeAdapter(MediaProbePort):
    def __init__(self, timeout_seconds: float = 30.0):
        self.timeout_seconds = timeout_seconds

    def inspect(self, path: Path) -> MediaInspection:
        if not shutil.which("ffprobe"):
            raise ExtractionError(
                code=ErrorCode.MEDIA_INSPECTION_FAILED,
                message="ffprobe binary not found on PATH",
                retryable=False,
                stage="inspection",
            )

        if not path.exists():
            raise ExtractionError(
                code=ErrorCode.ASSET_NOT_FOUND,
                message=f"Media file not found: {path}",
                retryable=False,
                stage="inspection",
            )

        file_size = path.stat().st_size
        if file_size == 0:
            raise ExtractionError(
                code=ErrorCode.MEDIA_INVALID_OR_CORRUPT,
                message="Media file is zero bytes",
                retryable=False,
                stage="inspection",
            )

        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(path),
        ]

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=True,
            )
        except subprocess.TimeoutExpired:
            raise ExtractionError(
                code=ErrorCode.MEDIA_INSPECTION_FAILED,
                message="ffprobe inspection timed out",
                retryable=True,
                stage="inspection",
            )
        except subprocess.CalledProcessError as e:
            raise ExtractionError(
                code=ErrorCode.MEDIA_INVALID_OR_CORRUPT,
                message=f"ffprobe failed to parse media: {e.stderr.strip()}",
                retryable=False,
                stage="inspection",
            )
        except Exception as e:
            raise ExtractionError(
                code=ErrorCode.MEDIA_INVALID_OR_CORRUPT,
                message=f"Failed to execute ffprobe: {e}",
                retryable=False,
                stage="inspection",
            )

        try:
            data = json.loads(res.stdout)
        except Exception as e:
            raise ExtractionError(
                code=ErrorCode.MEDIA_INVALID_OR_CORRUPT,
                message=f"Invalid JSON output from ffprobe: {e}",
                retryable=False,
                stage="inspection",
            )

        format_info = data.get("format", {})
        streams = data.get("streams", [])

        if not streams:
            raise ExtractionError(
                code=ErrorCode.MEDIA_NO_VIDEO_STREAM,
                message="No media streams found in file",
                retryable=False,
                stage="inspection",
            )

        video_streams = [s for s in streams if s.get("codec_type") == "video"]
        if not video_streams:
            raise ExtractionError(
                code=ErrorCode.MEDIA_NO_VIDEO_STREAM,
                message="No video stream found in media file (audio-only or image container)",
                retryable=False,
                stage="inspection",
            )

        warnings: List[str] = []
        if len(video_streams) > 1:
            warnings.append("MULTIPLE_VIDEO_STREAMS")

        # Pick default disposition or first video stream
        v_stream = next((s for s in video_streams if s.get("disposition", {}).get("default") == 1), video_streams[0])

        # Check for still images (single frame or no duration)
        nb_frames = v_stream.get("nb_frames")
        if nb_frames is not None:
            try:
                if int(nb_frames) <= 1:
                    raise ExtractionError(
                        code=ErrorCode.MEDIA_UNSUPPORTED_FORMAT,
                        message="Asset is a still image or has <= 1 frame",
                        retryable=False,
                        stage="inspection",
                    )
            except ValueError:
                pass

        width = int(v_stream.get("width", 0))
        height = int(v_stream.get("height", 0))
        if width <= 0 or height <= 0:
            raise ExtractionError(
                code=ErrorCode.MEDIA_INVALID_OR_CORRUPT,
                message="Invalid video dimensions",
                retryable=False,
                stage="inspection",
            )

        # Duration
        v_duration_str = v_stream.get("duration")
        f_duration_str = format_info.get("duration")

        duration_seconds = 0.0
        container_duration = None

        if f_duration_str:
            try:
                container_duration = float(f_duration_str)
            except ValueError:
                pass

        if v_duration_str:
            try:
                duration_seconds = float(v_duration_str)
            except ValueError:
                pass
        elif container_duration is not None:
            duration_seconds = container_duration

        if duration_seconds <= 0:
            raise ExtractionError(
                code=ErrorCode.MEDIA_UNSUPPORTED_FORMAT,
                message="Video duration is zero or undetermined",
                retryable=False,
                stage="inspection",
            )

        if v_duration_str and container_duration:
            if abs(duration_seconds - container_duration) > 0.1:
                warnings.append("DURATION_MISMATCH")

        # Rotation and display dimensions
        rotation = 0
        side_data_list = v_stream.get("side_data_list", [])
        for sd in side_data_list:
            if sd.get("side_data_type") == "Display Matrix":
                rot = sd.get("rotation", 0)
                rotation = int((-rot) % 360)
                break
        if rotation == 0:
            # fallback to tag
            tags = v_stream.get("tags", {})
            if "rotate" in tags:
                try:
                    rotation = int(tags["rotate"]) % 360
                except ValueError:
                    pass

        disp_w, disp_h = width, height
        if rotation in (90, 270):
            disp_w, disp_h = height, width

        # Frame rate
        avg_frame_rate = v_stream.get("avg_frame_rate", "0/1")
        frame_rate = None
        if avg_frame_rate and avg_frame_rate != "0/1":
            try:
                num, den = avg_frame_rate.split("/")
                if int(den) > 0:
                    frame_rate = float(Fraction(int(num), int(den)))
            except Exception:
                pass

        frame_rate_mode = "constant"
        # Check packets for VFR scan if available
        # Simplified detection: if r_frame_rate != avg_frame_rate or similar
        r_frame_rate = v_stream.get("r_frame_rate", "0/1")
        if r_frame_rate and avg_frame_rate and r_frame_rate != avg_frame_rate:
            frame_rate_mode = "variable"

        audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
        has_audio = len(audio_streams) > 0
        audio_codec = audio_streams[0].get("codec_name") if has_audio else None

        video_codec = v_stream.get("codec_name", "unknown")
        container_format = format_info.get("format_name", "unknown")
        video_time_base = v_stream.get("time_base")

        frame_count_int = None
        if nb_frames:
            try:
                frame_count_int = int(nb_frames)
            except ValueError:
                pass
        elif frame_rate and duration_seconds:
            frame_count_int = int(round(frame_rate * duration_seconds))

        start_time_us = 0
        start_time_str = v_stream.get("start_time")
        if start_time_str:
            try:
                start_time_us = int(float(start_time_str) * 1_000_000)
            except ValueError:
                pass

        return MediaInspection(
            duration_seconds=duration_seconds,
            container_duration_seconds=container_duration,
            width=width,
            height=height,
            display_width=disp_w,
            display_height=disp_h,
            rotation_degrees=rotation,
            pixel_aspect_ratio=v_stream.get("sample_aspect_ratio"),
            has_video=True,
            has_audio=has_audio,
            frame_rate=frame_rate,
            frame_rate_mode=frame_rate_mode,
            frame_count=frame_count_int,
            video_codec=video_codec,
            audio_codec=audio_codec,
            container_format=container_format,
            video_time_base=video_time_base,
            file_size_bytes=file_size,
            start_time_us=start_time_us,
            warnings=warnings,
            probe_name="ffprobe",
            probe_version="6.0",
        )
