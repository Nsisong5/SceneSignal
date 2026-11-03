"""Fake frame extraction adapter for testing."""

from pathlib import Path
from typing import List, Optional
from scene_signal.ports.frame_extraction import ExtractedFrame, FrameExtractionPort, FrameRequest


class FakeFrameExtractionAdapter(FrameExtractionPort):
    def __init__(self, fail_with: Optional[Exception] = None):
        self.fail_with = fail_with

    def extract(
        self,
        media_path: Path,
        requests: List[FrameRequest],
        out_dir: Path,
        max_long_edge: int = 1024,
    ) -> List[ExtractedFrame]:
        if self.fail_with:
            raise self.fail_with

        out_dir.mkdir(parents=True, exist_ok=True)
        extracted: List[ExtractedFrame] = []

        for i, req in enumerate(requests):
            img_path = out_dir / f"frame_{i+1:03d}.jpg"
            img_path.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00...")  # tiny placeholder JPEG bytes

            extracted.append(
                ExtractedFrame(
                    path=img_path,
                    requested_us=req.planned_time_us,
                    actual_us=req.planned_time_us,
                    pts=None,
                    time_base=None,
                    frame_index=i,
                    width=640,
                    height=360,
                    timestamp_source="decoded_pts",
                    warnings=[],
                )
            )

        return extracted
