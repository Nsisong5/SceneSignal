"""FFmpeg shot detection adapter (scene change and blackdetect)."""

import re
import shutil
import subprocess
from pathlib import Path
from scene_signal.domain.errors import ErrorCode, ExtractionError
from scene_signal.ports.shot_detection import (
    BlackInterval,
    BoundaryCandidate,
    ShotDetectionResult,
    ShotDetectionPort,
)


class FFmpegShotDetectionAdapter(ShotDetectionPort):
    def __init__(self, timeout_seconds: float = 60.0):
        self.timeout_seconds = timeout_seconds

    def detect(self, media_path: Path, threshold: float = 0.30) -> ShotDetectionResult:
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            raise ExtractionError(
                code=ErrorCode.SHOT_DETECTION_FAILED,
                message="ffmpeg/ffprobe binaries not found on PATH",
                retryable=False,
                stage="shot_detection",
            )

        if not media_path.exists():
            raise ExtractionError(
                code=ErrorCode.ASSET_NOT_FOUND,
                message=f"Media file not found: {media_path}",
                retryable=False,
                stage="shot_detection",
            )

        # Run ffmpeg with select filter for scene change detection and blackdetect
        cmd = [
            "ffmpeg",
            "-i", str(media_path),
            "-vf", f"select='gt(scene,{threshold})',metadata=print:file=-,blackdetect=d=0.5:pix_th=0.10",
            "-f", "null",
            "-",
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
                code=ErrorCode.SHOT_DETECTION_FAILED,
                message="Shot detection timed out",
                retryable=True,
                stage="shot_detection",
            )
        except Exception as e:
            raise ExtractionError(
                code=ErrorCode.SHOT_DETECTION_FAILED,
                message=f"Shot detection failed: {e}",
                retryable=False,
                stage="shot_detection",
            )

        boundaries: list[BoundaryCandidate] = []
        black_intervals: list[BlackInterval] = []

        combined_output = res.stdout + "\n" + res.stderr

        # Parse scene cuts from metadata output: pts_time:XYZ or similar
        # metadata format prints line like: pts:123 pts_time:3.000000
        # or scene score from select filter / metadata
        for line in combined_output.splitlines():
            if "pts_time:" in line:
                m = re.search(r"pts_time:([0-9.]+)", line)
                if m:
                    try:
                        sec = float(m.group(1))
                        us = int(sec * 1_000_000)
                        boundaries.append(
                            BoundaryCandidate(
                                time_us=us,
                                kind="hard_cut",
                                score=threshold,
                                score_meaning="scene_change_score",
                                uncertainty_us=41666,  # approx 1 frame at 24fps
                            )
                        )
                    except ValueError:
                        pass

            # Parse blackdetect: black_start:4.0 black_end:5.0
            if "black_start:" in line and "black_end:" in line:
                bs_m = re.search(r"black_start:([0-9.]+)", line)
                be_m = re.search(r"black_end:([0-9.]+)", line)
                if bs_m and be_m:
                    try:
                        start_us = int(float(bs_m.group(1)) * 1_000_000)
                        end_us = int(float(be_m.group(1)) * 1_000_000)
                        black_intervals.append(BlackInterval(start_us=start_us, end_us=end_us))
                        boundaries.append(BoundaryCandidate(time_us=start_us, kind="black_gap_start"))
                        boundaries.append(BoundaryCandidate(time_us=end_us, kind="black_gap_end"))
                    except ValueError:
                        pass

        return ShotDetectionResult(
            boundaries=boundaries,
            black_intervals=black_intervals,
            method_name="ffmpeg_scene",
            method_version="1.0",
            parameters={"threshold": threshold},
        )
