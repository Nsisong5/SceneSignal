import argparse
import sys
import json
from pathlib import Path
from decimal import Decimal
from scene_signal.render.domain.capabilities import RendererCapabilities
from scene_signal.render.domain.plan_validation import validate_edit_plan, validate_render_request
from scene_signal.render.domain.errors import RenderError
from scene_signal.render.contracts.export import export_schemas_to_dir
from scene_signal.render.domain.timing import derive_timeline
from scene_signal.render.domain.geometry import compute_fit
from scene_signal.render.contracts.render_request import RenderRequest
from scene_signal.render.contracts.render_result import OutputMetadata, ArtifactRef
from scene_signal.render.application.render_service import RenderService
from scene_signal.render.adapters.fakes.fake_resolver import FakeAssetResolver
from scene_signal.render.adapters.fakes.fake_inspector import FakeMediaInspector
from scene_signal.render.adapters.fakes.fake_engine import FakeRenderEngine
from scene_signal.render.adapters.fakes.fake_repository import FakeRenderRepository
from scene_signal.render.adapters.fakes.fake_workspace import FakeWorkspace
from scene_signal.render.adapters.fakes.fake_progress import FakeProgressReporter
from scene_signal.render.adapters.fakes.fake_clock import FakeClock
from scene_signal.render.adapters.fakes.fake_cancellation import FakeCancellationToken
from scene_signal.render.adapters.ffmpeg.binaries import FFmpegBinaries
from scene_signal.render.adapters.ffmpeg.inspector import FfprobeInspector
from scene_signal.render.adapters.ffmpeg.ffmpeg_engine import FFmpegRenderEngine
from scene_signal.render.adapters.storage.local_repository import LocalRenderRepository
from scene_signal.render.domain.postconditions import verify_output_postconditions

def main() -> None:
    parser = argparse.ArgumentParser(description="SceneSignal Timeline & Render Execution CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # capabilities
    subparsers.add_parser("capabilities", help="Print supported renderer capabilities")

    # doctor
    subparsers.add_parser("doctor", help="Check FFmpeg binaries and feature availability")

    # status
    status_parser = subparsers.add_parser("status", help="Get job status")
    status_parser.add_argument("job_id", help="Render job ID")
    status_parser.add_argument("--data-root", type=Path, required=True, help="Data root directory")

    # cleanup-stale
    clean_parser = subparsers.add_parser("cleanup-stale", help="Cleanup stale workspaces")
    clean_parser.add_argument("--older-than-hours", type=int, default=24, help="Age threshold in hours")
    clean_parser.add_argument("--data-root", type=Path, required=True, help="Data root directory")

    # inspect-source
    insp_parser = subparsers.add_parser("inspect-source", help="Inspect a source media file using ffprobe")
    insp_parser.add_argument("file_path", type=Path, help="Path to source media file")

    # inspect-output
    out_parser = subparsers.add_parser("inspect-output", help="Inspect an output media file")
    out_parser.add_argument("file_path", type=Path, help="Path to output media file")

    # verify-output
    verify_parser = subparsers.add_parser("verify-output", help="Verify output media against edit plan postconditions")
    verify_parser.add_argument("plan_path", type=Path, help="Path to edit plan JSON file")
    verify_parser.add_argument("output_path", type=Path, help="Path to rendered output file")

    # validate-plan
    val_parser = subparsers.add_parser("validate-plan", help="Validate an edit plan JSON file")
    val_parser.add_argument("plan_path", type=Path, help="Path to edit plan JSON file")

    # render
    render_parser = subparsers.add_parser("render", help="Execute real video render from edit plan")
    render_parser.add_argument("plan_path", type=Path, help="Path to edit plan JSON file")
    render_parser.add_argument("--assets-root", type=Path, required=True, help="Directory containing source assets")
    render_parser.add_argument("--data-root", type=Path, required=True, help="Directory for render repository and data")
    render_parser.add_argument("--job-id", default="render-job-001", help="Render job ID")
    render_parser.add_argument("--timeout", type=float, default=120.0, help="Timeout in seconds")

    # export-schemas
    exp_parser = subparsers.add_parser("export-schemas", help="Export JSON schemas")
    exp_parser.add_argument("--out", type=Path, required=True, help="Output directory for schemas")

    # timeline
    time_parser = subparsers.add_parser("timeline", help="Derive timeline and frame counts for a plan")
    time_parser.add_argument("plan_path", type=Path, help="Path to edit plan JSON file")
    time_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # geometry
    geom_parser = subparsers.add_parser("geometry", help="Compute fit and scaling geometry")
    geom_parser.add_argument("--src", required=True, help="Source dimensions as WxH (e.g. 1080x1920)")
    geom_parser.add_argument("--sar", default="1:1", help="Sample aspect ratio as n:d")
    geom_parser.add_argument("--rotation", type=int, default=0, choices=[0, 90, 180, 270], help="Rotation")
    geom_parser.add_argument("--out", required=True, help="Output dimensions as WxH (e.g. 1280x720)")
    geom_parser.add_argument("--fit", default="letterbox", choices=["letterbox", "crop"], help="Fit mode")

    # demo-fake
    demo_parser = subparsers.add_parser("demo-fake", help="Demonstrate render lifecycle with fakes")
    demo_parser.add_argument("plan_path", type=Path, help="Path to edit plan JSON file")
    demo_parser.add_argument("--out", type=Path, required=True, help="Output directory for demo artifacts")
    demo_parser.add_argument("--job-id", default="demo-job-001", help="Render job ID")

    args = parser.parse_args()

    try:
        if args.command == "capabilities":
            caps = RendererCapabilities()
            print(json.dumps(caps.model_dump(mode="json"), indent=2))
            sys.exit(0)

        elif args.command == "doctor":
            try:
                caps = FFmpegBinaries.verify()
                print("FFmpeg System Check:")
                print(f"  - ffmpeg: {'✓' if caps['ffmpeg'] else '✗'}")
                print(f"  - ffprobe: {'✓' if caps['ffprobe'] else '✗'}")
                print(f"  - libx264: {'✓' if caps['libx264'] else '✗'}")
                print(f"  - aac: {'✓' if caps['aac'] else '✗'}")
                print(f"  - xfade: {'✓' if caps['xfade'] else '✗'}")
                print(f"  - acrossfade: {'✓' if caps['acrossfade'] else '✗'}")
                sys.exit(0)
            except RenderError as e:
                print(f"Doctor Check Failed: {e.message}", file=sys.stderr)
                sys.exit(2)

        elif args.command == "status":
            repo = LocalRenderRepository(args.data_root)
            st = repo.get_status(args.job_id)
            if not st:
                print(f"Job not found: {args.job_id}", file=sys.stderr)
                sys.exit(4)
            print(json.dumps({"job_id": args.job_id, "status": st}, indent=2))
            sys.exit(0)

        elif args.command == "cleanup-stale":
            repo = LocalRenderRepository(args.data_root)
            count = repo.cleanup_stale(args.older_than_hours)
            print(f"Cleaned up {count} stale workspaces.")
            sys.exit(0)

        elif args.command == "inspect-source":
            path: Path = args.file_path
            if not path.exists():
                print(f"Error: File not found: {path}", file=sys.stderr)
                sys.exit(2)
            inspector = FfprobeInspector()
            try:
                info = inspector.inspect(path)
                print(json.dumps(info.model_dump(mode="json"), indent=2))
                sys.exit(0)
            except RenderError as e:
                print(json.dumps(e.to_error_info().model_dump(mode="json"), indent=2), file=sys.stderr)
                sys.exit(2)

        elif args.command == "inspect-output":
            path: Path = args.file_path
            if not path.exists():
                print(f"Error: File not found: {path}", file=sys.stderr)
                sys.exit(2)
            inspector = FfprobeInspector()
            try:
                info = inspector.inspect(path)
                meta = OutputMetadata(
                    ref=ArtifactRef(scheme="file", uri=str(path)),
                    container="mp4",
                    video_codec=info.video_codec,
                    audio_codec=info.audio.codec if info.audio else None,
                    duration_seconds=info.duration_seconds,
                    width=info.width,
                    height=info.height,
                    frame_rate=str(info.frame_rate),
                    frame_count=int(info.duration_seconds * info.frame_rate),
                    has_video=info.has_video,
                    has_audio=info.has_audio,
                    file_size_bytes=path.stat().st_size,
                )
                print(json.dumps(meta.model_dump(mode="json"), indent=2))
                sys.exit(0)
            except RenderError as e:
                print(json.dumps(e.to_error_info().model_dump(mode="json"), indent=2), file=sys.stderr)
                sys.exit(2)

        elif args.command == "verify-output":
            plan_path: Path = args.plan_path
            out_path: Path = args.output_path
            if not plan_path.exists() or not out_path.exists():
                print(f"Error: Plan or output file not found", file=sys.stderr)
                sys.exit(2)

            plan = validate_edit_plan(plan_path.read_bytes())
            inspector = FfprobeInspector()
            info = inspector.inspect(out_path)
            meta = OutputMetadata(
                ref=ArtifactRef(scheme="file", uri=str(out_path)),
                container="mp4",
                video_codec=info.video_codec,
                audio_codec=info.audio.codec if info.audio else None,
                duration_seconds=info.duration_seconds,
                width=info.width,
                height=info.height,
                frame_rate=str(info.frame_rate),
                frame_count=int(info.duration_seconds * info.frame_rate),
                has_video=info.has_video,
                has_audio=info.has_audio,
                file_size_bytes=out_path.stat().st_size,
            )
            checks = verify_output_postconditions(out_path, meta, plan)
            failed = [c for c in checks if c.status != "passed"]
            for c in checks:
                print(f"  [{c.status.upper()}] {c.check}: {c.detail}")
            if failed:
                sys.exit(2)
            sys.exit(0)

        elif args.command == "render":
            path: Path = args.plan_path
            assets_root: Path = args.assets_root
            data_root: Path = args.data_root
            job_id: str = args.job_id
            timeout: float = args.timeout

            if not path.exists():
                print(f"Error: Plan file not found: {path}", file=sys.stderr)
                sys.exit(2)

            plan_data = validate_edit_plan(path.read_bytes())
            req = RenderRequest(render_job_id=job_id, plan=plan_data)

            resolver = FakeAssetResolver(assets_root=assets_root)
            inspector = FfprobeInspector()
            engine = FFmpegRenderEngine()
            repository = LocalRenderRepository(data_root)
            workspace_factory = FakeWorkspace(data_root / "work" / job_id)
            clock = FakeClock()

            service = RenderService(
                resolver=resolver,
                inspector=inspector,
                engine=engine,
                repository=repository,
                workspace_factory=workspace_factory,
                clock=clock,
            )

            progress = FakeProgressReporter()
            cancel_token = FakeCancellationToken()

            try:
                res = service.render(req, progress, cancel_token)
                print(f"Render succeeded! Status: {res.status}")
                print(f"Manifest ref: {res.manifest_ref.uri}")
                sys.exit(0)
            except RenderError as e:
                print(json.dumps(e.to_error_info().model_dump(mode="json"), indent=2), file=sys.stderr)
                sys.exit(2)

        elif args.command == "validate-plan":
            path: Path = args.plan_path
            if not path.exists():
                print(f"Error: Plan file not found: {path}", file=sys.stderr)
                sys.exit(2)
            content = path.read_bytes()
            try:
                validate_edit_plan(content)
                print("OK")
                sys.exit(0)
            except RenderError as e:
                print(json.dumps(e.to_error_info().model_dump(mode="json"), indent=2), file=sys.stderr)
                sys.exit(2)

        elif args.command == "export-schemas":
            out_dir: Path = args.out
            paths = export_schemas_to_dir(out_dir)
            print(f"Exported {len(paths)} schemas to {out_dir}")
            for name in paths:
                print(f"  - {name}")
            sys.exit(0)

        elif args.command == "timeline":
            path: Path = args.plan_path
            if not path.exists():
                print(f"Error: Plan file not found: {path}", file=sys.stderr)
                sys.exit(2)
            content = path.read_bytes()
            try:
                plan = validate_edit_plan(content)
                derived = derive_timeline(plan)
                if args.json:
                    print(json.dumps(derived.model_dump(mode="json"), indent=2))
                else:
                    print(f"Timeline Summary (FPS: {derived.fps}, Total Frames: {derived.total_frames}, Duration: {float(derived.derived_duration_seconds)}s):")
                    for s in derived.segments:
                        print(f"  Segment {s.index} ({s.segment_id}): asset={s.asset_id}, source={s.source_start_seconds}-{s.source_end_seconds}s, timeline={s.timeline_start_seconds}-{s.timeline_end_seconds}s, frames={s.frame_start}..{s.frame_start + s.frame_count} (count={s.frame_count})")
                sys.exit(0)
            except RenderError as e:
                print(json.dumps(e.to_error_info().model_dump(mode="json"), file=sys.stderr), file=sys.stderr)
                sys.exit(2)

        elif args.command == "geometry":
            src_parts = args.src.lower().split("x")
            out_parts = args.out.lower().split("x")
            sar_parts = args.sar.split(":")
            src_w, src_h = int(src_parts[0]), int(src_parts[1])
            out_w, out_h = int(out_parts[0]), int(out_parts[1])
            sar_n, sar_d = int(sar_parts[0]), int(sar_parts[1])

            res = compute_fit(
                src_width=src_w,
                src_height=src_h,
                sar_num=sar_n,
                sar_den=sar_d,
                rotation=args.rotation,
                target_width=out_w,
                target_height=out_h,
                fit_mode=args.fit,
            )
            print(json.dumps(res._asdict(), indent=2))
            sys.exit(0)

        elif args.command == "demo-fake":
            path: Path = args.plan_path
            out_dir: Path = args.out
            if not path.exists():
                print(f"Error: Plan file not found: {path}", file=sys.stderr)
                sys.exit(2)
            
            plan_data = validate_edit_plan(path.read_bytes())
            req = RenderRequest(render_job_id=args.job_id, plan=plan_data)

            resolver = FakeAssetResolver(assets_root=path.parent)
            inspector = FakeMediaInspector()
            engine = FakeRenderEngine()
            repository = FakeRenderRepository()
            workspace_factory = FakeWorkspace(out_dir / "work")
            clock = FakeClock()

            service = RenderService(
                resolver=resolver,
                inspector=inspector,
                engine=engine,
                repository=repository,
                workspace_factory=workspace_factory,
                clock=clock,
            )

            progress = FakeProgressReporter()
            cancel_token = FakeCancellationToken()

            try:
                res = service.render(req, progress, cancel_token)
                out_dir.mkdir(parents=True, exist_ok=True)
                (out_dir / "request.json").write_text(json.dumps(req.model_dump(mode="json"), indent=2))
                (out_dir / "status.json").write_text(json.dumps({"status": res.status}, indent=2))
                (out_dir / "result.json").write_text(json.dumps(res.model_dump(mode="json"), indent=2))
                manifest = repository.jobs[args.job_id]["manifest"]
                if manifest:
                    (out_dir / "manifest.json").write_text(json.dumps(manifest.model_dump(mode="json"), indent=2))
                
                fake_out = out_dir / "work" / "output.mp4"
                if fake_out.exists():
                    (out_dir / "output.mp4").write_bytes(fake_out.read_bytes())

                print(f"Demo render succeeded! Artifacts written to {out_dir}")
                sys.exit(0)
            except RenderError as e:
                print(json.dumps(e.to_error_info().model_dump(mode="json"), indent=2), file=sys.stderr)
                sys.exit(1)

    except Exception as e:
        print(f"Internal Error: {e}", file=sys.stderr)
        sys.exit(3)

if __name__ == "__main__":
    main()
