"""Command line interface for SceneSignal."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from scene_signal import __version__
from scene_signal.domain.errors import ErrorCode, ExtractionError
from scene_signal.schemas.export import export_schemas
from scene_signal.schemas.job import parse_extraction_job
from scene_signal.schemas.result import SceneIntelligenceDocument


def main() -> None:
    parser = argparse.ArgumentParser(description="SceneSignal: Turn video into timestamped editing intelligence.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # validate-request
    req_parser = subparsers.add_parser("validate-request", help="Validate an ExtractionJob JSON file.")
    req_parser.add_argument("file", type=Path, help="Path to JSON file.")

    # validate-result
    res_parser = subparsers.add_parser("validate-result", help="Validate a SceneIntelligenceDocument JSON file.")
    res_parser.add_argument("file", type=Path, help="Path to JSON file.")

    # export-schemas
    exp_parser = subparsers.add_parser("export-schemas", help="Export JSON schemas.")
    exp_parser.add_argument("--out", type=Path, required=True, help="Output directory.")

    # inspect
    insp_parser = subparsers.add_parser("inspect", help="Inspect a video file and print MediaInspection JSON.")
    insp_parser.add_argument("file", type=Path, help="Path to video file.")

    # extract-frames
    ef_parser = subparsers.add_parser("extract-frames", help="Extract frames from video at specified times.")
    ef_parser.add_argument("file", type=Path, help="Path to video file.")
    ef_parser.add_argument("--times", required=True, help="Comma-separated timestamps in seconds.")
    ef_parser.add_argument("--out", type=Path, required=True, help="Output directory.")
    ef_parser.add_argument("--long-edge", type=int, default=1024, help="Max long edge for downscaling.")

    # detect-shots
    ds_parser = subparsers.add_parser("detect-shots", help="Detect shots and boundaries in a video file.")
    ds_parser.add_argument("file", type=Path, help="Path to video file.")
    ds_parser.add_argument("--threshold", type=float, default=0.30, help="Scene detection threshold.")

    # doctor
    doc_parser = subparsers.add_parser("doctor", help="Report environment, FFmpeg/ffprobe versions, and settings.")

    # extract
    ext_parser = subparsers.add_parser("extract", help="Run scene intelligence extraction pipeline.")
    ext_parser.add_argument("file", type=Path, nargs="?", help="Path to video file (convenience form).")
    ext_parser.add_argument("--job", type=Path, help="Path to ExtractionJob JSON file.")
    ext_parser.add_argument("--assets-root", type=Path, default=Path.cwd(), help="Assets root directory.")
    ext_parser.add_argument("--provider", default="fake", help="Vision provider name.")
    ext_parser.add_argument("--out", type=Path, default=Path("out_extraction"), help="Output directory.")
    ext_parser.add_argument("--profile", default="standard", help="Extraction profile.")
    ext_parser.add_argument("--capabilities", default="visual_observations,temporal_events,shot_detection,camera_analysis", help="Comma-separated capabilities.")
    ext_parser.add_argument("--job-id", default="job-demo-001", help="Job ID for convenience form.")
    ext_parser.add_argument("--source-kind", default="generated", choices=["generated", "user_upload", "imported"], help="Source kind.")
    ext_parser.add_argument("--data-root", type=Path, help="Data root directory for persistence and repository.")
    ext_parser.add_argument("--rerun-of", help="Rerun of job ID.")
    ext_parser.add_argument("--fake-fail", help="Failure injection for fake provider.")

    # status
    status_parser = subparsers.add_parser("status", help="Get status of a job.")
    status_parser.add_argument("job_id", help="Job ID.")
    status_parser.add_argument("--data-root", type=Path, required=True, help="Data root directory.")

    # result
    res_cli_parser = subparsers.add_parser("result", help="Get result of a job.")
    res_cli_parser.add_argument("job_id", help="Job ID.")
    res_cli_parser.add_argument("--data-root", type=Path, required=True, help="Data root directory.")

    args = parser.parse_args()

    try:
        if args.command == "doctor":
            from scene_signal.domain.policies import Settings
            settings = Settings.load()
            ffmpeg_version = "not found"
            ffprobe_version = "not found"
            try:
                res = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=3)
                if res.returncode == 0:
                    ffmpeg_version = res.stdout.splitlines()[0]
            except Exception:
                pass
            try:
                res = subprocess.run(["ffprobe", "-version"], capture_output=True, text=True, timeout=3)
                if res.returncode == 0:
                    ffprobe_version = res.stdout.splitlines()[0]
            except Exception:
                pass

            report = {
                "python_version": sys.version,
                "ffmpeg": ffmpeg_version,
                "ffprobe": ffprobe_version,
                "settings": {
                    "log_level": settings.log_level,
                    "timeout_seconds": settings.timeout_seconds,
                },
            }
            if args.json:
                print(json.dumps(report, indent=2))
            else:
                print(f"Python Version: {report['python_version']}")
                print(f"FFmpeg: {report['ffmpeg']}")
                print(f"FFprobe: {report['ffprobe']}")
                print(f"Settings: {report['settings']}")
            sys.exit(0)

        elif args.command == "validate-request":
            if not args.file.exists():
                err = {"code": "ASSET_NOT_FOUND", "message": f"File not found: {args.file}"}
                print(json.dumps(err) if args.json else err["message"], file=sys.stderr)
                sys.exit(2)
            content = args.file.read_text(encoding="utf-8")
            parse_extraction_job(content)
            print("OK")
        elif args.command == "validate-result":
            if not args.file.exists():
                err = {"code": "ASSET_NOT_FOUND", "message": f"File not found: {args.file}"}
                print(json.dumps(err) if args.json else err["message"], file=sys.stderr)
                sys.exit(2)
            content = args.file.read_text(encoding="utf-8")
            data = json.loads(content)
            SceneIntelligenceDocument.model_validate(data)
            print("OK")
        elif args.command == "export-schemas":
            export_schemas(args.out)
            print("OK")
        elif args.command == "inspect":
            from scene_signal.adapters.media.ffprobe import FFprobeAdapter
            adapter = FFprobeAdapter()
            inspection = adapter.inspect(args.file)
            print(json.dumps(inspection.__dict__, indent=2))
        elif args.command == "extract-frames":
            from scene_signal.adapters.media.ffmpeg_frames import FFmpegFrameExtractionAdapter
            from scene_signal.ports.frame_extraction import FrameRequest
            times = [float(t.strip()) for t in args.times.split(",")]
            requests = [FrameRequest(planned_time_us=int(t * 1_000_000)) for t in times]
            adapter = FFmpegFrameExtractionAdapter()
            frames = adapter.extract(args.file, requests, args.out, max_long_edge=1024)
            table = []
            for f in frames:
                table.append({
                    "path": str(f.path),
                    "requested_s": f.requested_us / 1_000_000.0,
                    "actual_s": f.actual_us / 1_000_000.0,
                    "width": f.width,
                    "height": f.height,
                    "source": f.timestamp_source,
                })
            print(json.dumps(table, indent=2))
        elif args.command == "detect-shots":
            from scene_signal.adapters.media.ffmpeg_shots import FFmpegShotDetectionAdapter
            from scene_signal.application.shots import build_shots
            from scene_signal.domain.policies import ShotPolicy
            adapter = FFmpegShotDetectionAdapter()
            result = adapter.detect(args.file, threshold=args.threshold)
            shots, warnings = build_shots(result, 5_000_000, ShotPolicy(), requested=True)
            output = {
                "boundaries": [b.__dict__ for b in result.boundaries],
                "black_intervals": [bi.__dict__ for bi in result.black_intervals],
                "shots": [s.__dict__ for s in shots],
                "warnings": warnings,
                "limitations": result.limitations,
            }
            print(json.dumps(output, indent=2))
        elif args.command == "status":
            from scene_signal.adapters.storage.local_repository import LocalJobRepositoryAdapter
            repo = LocalJobRepositoryAdapter(args.data_root)
            st = repo.load_status(args.job_id)
            if st:
                print(st.status)
            else:
                print("not_found", file=sys.stderr)
                sys.exit(1)
        elif args.command == "result":
            from scene_signal.adapters.storage.local_repository import LocalJobRepositoryAdapter
            repo = LocalJobRepositoryAdapter(args.data_root)
            res = repo.load_result(args.job_id)
            if res and res.document:
                print(json.dumps(res.document.model_dump(mode="json"), indent=2))
            else:
                print("not_found", file=sys.stderr)
                sys.exit(1)
        elif args.command == "extract":
            from scene_signal.adapters.storage.local_fs import LocalFilesystemStorageAdapter
            from scene_signal.adapters.media.ffprobe import FFprobeAdapter
            from scene_signal.adapters.media.ffmpeg_frames import FFmpegFrameExtractionAdapter
            from scene_signal.adapters.media.ffmpeg_shots import FFmpegShotDetectionAdapter
            from scene_signal.adapters.fakes.fake_vision import FakeVisionAdapter
            from scene_signal.adapters.storage.local_repository import LocalJobRepositoryAdapter
            from scene_signal.application.pipeline import PipelinePorts
            from scene_signal.application.service import SceneIntelligenceService

            if args.job:
                if not args.job.exists():
                    err = {"code": "ASSET_NOT_FOUND", "message": f"Job file not found: {args.job}"}
                    print(json.dumps(err) if args.json else err["message"], file=sys.stderr)
                    sys.exit(2)
                job_content = args.job.read_text(encoding="utf-8")
                job = parse_extraction_job(job_content)
            elif args.file:
                caps_list = [c.strip() for c in args.capabilities.split(",")]
                job_dict = {
                    "contract_version": "1.0",
                    "job_id": args.job_id,
                    "asset_id": f"asset-{args.file.stem}",
                    "source_kind": args.source_kind,
                    "asset_ref": {"scheme": "file", "uri": str(args.file)},
                    "extraction_profile": args.profile,
                    "requested_capabilities": caps_list,
                }
                if args.rerun_of:
                    job_dict["rerun_of"] = args.rerun_of
                job = parse_extraction_job(job_dict)
                if not args.json:
                    print(f"Built Job Document:\n{json.dumps(job_dict, indent=2)}")
            else:
                err = {"code": "INVALID_JOB_CONTRACT", "message": "Either --job or media file argument must be provided"}
                print(json.dumps(err) if args.json else err["message"], file=sys.stderr)
                sys.exit(2)

            fail_with = None
            if args.fake_fail:
                if "timeout" in args.fake_fail:
                    from scene_signal.ports.visual_analysis import ProviderTimeout
                    fail_with = ProviderTimeout("Injected timeout")
                elif "rate_limit" in args.fake_fail:
                    from scene_signal.ports.visual_analysis import ProviderRateLimited
                    fail_with = ProviderRateLimited("Injected rate limit", retry_after_seconds=1.0)
                elif "unavailable" in args.fake_fail:
                    from scene_signal.ports.visual_analysis import ProviderUnavailable
                    fail_with = ProviderUnavailable("Injected unavailable")

            repo = LocalJobRepositoryAdapter(args.data_root) if args.data_root else None
            ports = PipelinePorts(
                storage=LocalFilesystemStorageAdapter(),
                media_probe=FFprobeAdapter(),
                frame_extraction=FFmpegFrameExtractionAdapter(),
                shot_detection=FFmpegShotDetectionAdapter(),
                vision=FakeVisionAdapter(fail_with=fail_with),
                repository=repo,
            )
            service = SceneIntelligenceService(ports=ports, allowed_roots=[args.assets_root])
            result = service.extract(job)

            args.out.mkdir(parents=True, exist_ok=True)
            res_path = args.out / "result.json"
            if result.status in ("succeeded", "partial") and result.document:
                res_path.write_text(json.dumps(result.document.model_dump(mode="json"), indent=2, sort_keys=True) + "\n", encoding="utf-8")
                if not args.json:
                    print(f"Extraction succeeded with outcome: {result.document.outcome}")
                    print(f"Result written to {res_path}")
                    print(f"Shots: {len(result.document.shots)}, Frames: {len(result.document.frames)}")
                sys.exit(0 if result.status == "succeeded" else 1)
            else:
                err_obj = result.error.model_dump(mode="json") if result.error else {"code": "FAILED", "message": "Extraction failed"}
                print(json.dumps(err_obj, indent=2) if args.json else err_obj["message"], file=sys.stderr)
                sys.exit(1)
    except ExtractionError as e:
        output = {"code": e.code.value if hasattr(e.code, "value") else str(e.code), "message": e.message, "details": e.details}
        print(json.dumps(output) if getattr(args, "json", False) else output["message"], file=sys.stderr)
        sys.exit(2 if e.code in (ErrorCode.INVALID_JOB_CONTRACT, ErrorCode.UNSUPPORTED_CONTRACT_VERSION, ErrorCode.ASSET_NOT_FOUND) else 1)
    except Exception as e:
        output = {"code": "INTERNAL_ERROR", "message": str(e), "details": {}}
        print(json.dumps(output) if getattr(args, "json", False) else output["message"], file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
