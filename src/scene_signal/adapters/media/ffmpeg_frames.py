"""FFmpeg frame extraction adapter."""

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from scene_signal.domain.errors import ErrorCode, ExtractionError
from scene_signal.ports.frame_extraction import ExtractedFrame, FrameExtractionPort, FrameRequest


class FFmpegFrameExtractionAdapter(FrameExtractionPort):
    def __init__(self, timeout_seconds: float = 30.0):
        self.timeout_seconds = timeout_seconds

    def extract(
        self,
        media_path: Path,
        requests: List[FrameRequest],
        out_dir: Path,
        max_long_edge: int = 1024,
    ) -> List[ExtractedFrame]:
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            raise ExtractionError(
                code=ErrorCode.FRAME_EXTRACTION_FAILED,
                message="ffmpeg/ffprobe binaries not found on PATH",
                retryable=False,
                stage="frame_extraction",
            )

        out_dir.mkdir(parents=True, exist_ok=True)
        extracted: List[ExtractedFrame] = []

        for i, req in enumerate(requests):
            req_sec = req.planned_time_us / 1_000_000.0
            out_img = out_dir / f"frame_{i+1:03d}.jpg"

            # Scale filter: downscale if long edge > max_long_edge, never upscale
            # scale='if(gt(iw,ih),min(iw,{m}),-1)':'if(gt(iw,ih),-1,min(ih,{m}))'
            scale_filter = f"scale='if(gt(iw,ih),min(iw,{max_long_edge}),-1)':'if(gt(iw,ih),-1,min(ih,{max_long_edge}))',fps=1/1000"

            cmd = [
                "ffmpeg",
                "-y",
                "-ss", str(req_sec),
                "-i", str(media_path),
                "-frames:v", "1",
                "-q:v", "3",
                "-vf", "showinfo",
                str(out_img),
            ]

            try:
                res = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                )
            except subprocess.TimeoutExpired:
                raise ExtractionError(
                    code=ErrorCode.FRAME_EXTRACTION_FAILED,
                    message=f"Frame extraction timed out at {req_sec}s",
                    retryable=True,
                    stage="frame_extraction",
                )
            except Exception as e:
                raise ExtractionError(
                    code=ErrorCode.FRAME_EXTRACTION_FAILED,
                    message=f"Failed to execute ffmpeg for frame extraction: {e}",
                    retryable=False,
                    stage="frame_extraction",
                )

            # Check if output image exists
            if not out_img.exists() or out_img.stat().st_size == 0:
                # Fallback / retry without -ss or handle edge case
                # If frame extraction failed or timed out / requested time >= duration
                raise ExtractionError(
                    code=ErrorCode.FRAME_EXTRACTION_FAILED,
                    message=f"Failed to extract frame at {req_sec}s",
                    retryable=False,
                    stage="frame_extraction",
                )

            # Parse actual timestamp from showinfo stderr
            actual_us = req.planned_time_us
            timestamp_source = "requested_unverified"
            warnings = []
            pts = None
            time_base = None

            stderr_output = res.stderr
            match = re.search(r"pts_time:([0-9.]+)", stderr_output)
            if match:
                try:
                    pts_time_sec = float(match.group(1))
                    actual_us = int(pts_time_sec * 1_000_000)
                    timestamp_source = "decoded_pts"
                except ValueError:
                    warnings.append("TIMESTAMP_UNVERIFIED")
            else:
                warnings.append("TIMESTAMP_UNVERIFIED")

            # Get image dimensions using ffprobe
            width, height = 1024, 576
            try:
                probe_cmd = [
                    "ffprobe",
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_streams",
                    str(out_img),
                ]
                p_res = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=5)
                p_data = json.loads(p_res.stdout)
                for s in p_data.get("streams", []):
                    if s.get("codec_type") == "video":
                        width = int(s.get("width", width))
                        height = int(s.get("height", height))
                        break
            except Exception:
                pass

            extracted.append(
                ExtractedFrame(
                    path=out_img,
                    requested_us=req.planned_time_us,
                    actual_us=actual_us,
                    pts=pts,
                    time_base=time_base,
                    frame_index=None,
                    width=width,
                    height=height,
                    timestamp_source=timestamp_source,
                    warnings=warnings,
                )
            )

        return extracted
