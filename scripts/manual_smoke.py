"""Manual smoke test script running fixtures through the SceneSignal pipeline."""

import json
import sys
from pathlib import Path
from scene_signal.adapters.storage.local_fs import LocalFilesystemStorageAdapter
from scene_signal.adapters.media.ffprobe import FFprobeAdapter
from scene_signal.adapters.media.ffmpeg_frames import FFmpegFrameExtractionAdapter
from scene_signal.adapters.media.ffmpeg_shots import FFmpegShotDetectionAdapter
from scene_signal.adapters.fakes.fake_vision import FakeVisionAdapter
from scene_signal.application.pipeline import PipelinePorts
from scene_signal.application.service import SceneIntelligenceService
from scene_signal.schemas.job import parse_extraction_job


def run_smoke() -> None:
    jobs_dir = Path("tests/fixtures/jobs")
    if not jobs_dir.exists():
        print("Job documents not found. Run python scripts/make_job_documents.py first.", file=sys.stderr)
        sys.exit(1)

    ports = PipelinePorts(
        storage=LocalFilesystemStorageAdapter(),
        media_probe=FFprobeAdapter(),
        frame_extraction=FFmpegFrameExtractionAdapter(),
        shot_detection=FFmpegShotDetectionAdapter(),
        vision=FakeVisionAdapter(),
    )
    service = SceneIntelligenceService(ports=ports, allowed_roots=[Path("tests/fixtures/media")])

    print(f"{'FIXTURE':<35} | {'STATUS':<10} | {'OUTCOME':<10} | {'SHOTS':<6} | {'FRAMES':<6} | {'OBS':<6} | {'EVENTS':<6}")
    print("-" * 95)

    failed_any = False
    for job_file in sorted(jobs_dir.glob("*.json")):
        try:
            job_data = job_file.read_text(encoding="utf-8")
            job = parse_extraction_job(job_data)
            result = service.extract(job)

            status = result.status
            outcome = result.document.outcome if result.document else "N/A"
            shots = len(result.document.shots) if result.document else 0
            frames = len(result.document.frames) if result.document else 0
            obs = len(result.document.observations) if result.document else 0
            events = len(result.document.events) if result.document else 0

            print(f"{job_file.name:<35} | {status:<10} | {outcome:<10} | {shots:<6} | {frames:<6} | {obs:<6} | {events:<6}")
            if status == "failed":
                failed_any = True
        except Exception as e:
            print(f"{job_file.name:<35} | {'ERROR':<10} | {'N/A':<10} | {0:<6} | {0:<6} | {0:<6} | {0:<6} -> {e}")
            failed_any = True

    if failed_any:
        print("\nSome smoke tests failed.")
        sys.exit(1)
    else:
        print("\nAll smoke tests passed successfully.")
        sys.exit(0)


if __name__ == "__main__":
    run_smoke()
