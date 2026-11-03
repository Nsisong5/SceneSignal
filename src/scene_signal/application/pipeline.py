"""Extraction pipeline orchestration with retries, repository persistence, and partial results."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from scene_signal.domain.policies import Settings
from scene_signal.domain.canonical import request_hash
from scene_signal.schemas.job import ExtractionJob, parse_extraction_job
from scene_signal.schemas.result import JobResult, JobStatusRecord
from scene_signal.ports.asset_storage import AssetStoragePort, Workspace
from scene_signal.ports.media_probe import MediaProbePort
from scene_signal.ports.frame_extraction import FrameExtractionPort, FrameRequest
from scene_signal.ports.shot_detection import ShotDetectionPort
from scene_signal.ports.visual_analysis import VisualAnalysisPort, VisionAnalysisRequest, VisionMode
from scene_signal.ports.repository import JobRepositoryPort
from scene_signal.application.sampling import plan_sampling
from scene_signal.application.shots import build_shots
from scene_signal.application.provider_response import negotiate, validate_response
from scene_signal.application.assembler import assemble_document
from scene_signal.application.document_validator import assert_valid_document
from scene_signal.application.provenance import build_provenance
from scene_signal.application.retry import RetryExecutor
from scene_signal.domain.errors import ExtractionError, ErrorCode


@dataclass(frozen=True)
class PipelinePorts:
    storage: AssetStoragePort
    media_probe: MediaProbePort
    frame_extraction: FrameExtractionPort
    shot_detection: ShotDetectionPort
    vision: VisualAnalysisPort
    repository: Optional[JobRepositoryPort] = None


class ExtractionPipeline:
    def __init__(self, ports: PipelinePorts, settings: Optional[Settings] = None, allowed_roots: Optional[List[Path]] = None):
        self.ports = ports
        self.settings = settings or Settings.load()
        self.allowed_roots = allowed_roots or [Path.cwd()]
        self.retry_executor = RetryExecutor(
            max_attempts=self.settings.retry.max_attempts,
            initial_delay_seconds=self.settings.retry.initial_delay_seconds,
            backoff_factor=self.settings.retry.backoff_factor,
            max_delay_seconds=self.settings.retry.max_delay_seconds,
        )

    def run(self, job: ExtractionJob) -> JobResult:
        started_at = datetime.now(timezone.utc).isoformat()
        req_hash = request_hash(job)
        stage_attempts = {}

        if self.ports.repository:
            try:
                claim_status = self.ports.repository.claim_job(job, req_hash)
                if claim_status == "idempotent_hit":
                    res = self.ports.repository.load_result(job.job_id)
                    if res:
                        return res
            except ExtractionError as e:
                return JobResult(
                    job_id=job.job_id,
                    status="failed",
                    error={
                        "code": e.code.value if hasattr(e.code, "value") else str(e.code),
                        "message": e.message,
                        "retryable": e.retryable,
                        "stage": e.stage,
                        "attempts": 1,
                        "details": e.details,
                    },
                )

        workspace = Workspace(job.job_id)
        try:
            with workspace:
                # Stage 2: Resolve asset
                stage_attempts["resolve"] = 1
                resolved = self.ports.storage.resolve(job.asset_ref, self.allowed_roots)

                # Stage 3: Inspect media
                stage_attempts["inspect"] = 1
                inspection = self.ports.media_probe.inspect(resolved.path)

                # Stage 4a: Shot detection
                stage_attempts["shot_detection"] = 1
                shot_detection_requested = "shot_detection" in job.requested_capabilities or not job.requested_capabilities
                shot_result = None
                if shot_detection_requested:
                    shot_result = self.ports.shot_detection.detect(resolved.path, threshold=self.settings.shot.scene_threshold)

                shot_drafts, shot_warnings = build_shots(
                    shot_result,
                    int(inspection.duration_seconds * 1_000_000),
                    self.settings.shot,
                    requested=shot_detection_requested,
                )

                # Stage 4b: Sampling plan
                profile = self.settings.profiles.get(job.extraction_profile, self.settings.profiles["standard"])
                intervals = []
                for sd in shot_drafts:
                    from scene_signal.domain.timeline import Interval, TimeUs
                    intervals.append(Interval(TimeUs(sd.start_us), TimeUs(sd.end_us)))
                sampling_plan = plan_sampling(int(inspection.duration_seconds * 1_000_000), intervals, profile)

                # Stage 5: Extract frames
                stage_attempts["frame_extraction"] = 1
                frame_requests = [FrameRequest(s.planned_time_us) for s in sampling_plan.samples]
                frames_dir = workspace.sub_dir("frames")
                extracted_frames = self.ports.frame_extraction.extract(
                    resolved.path, frame_requests, frames_dir, max_long_edge=1024
                )

                # Stage 6: Analyze (vision) with retries & partial results support
                vision_caps = self.ports.vision.capabilities()
                vision_results = []
                capability_reports = []
                analyze_attempts = 1
                analysis_failed = False

                for i, sd in enumerate(shot_drafts):
                    sid = f"shot-{i+1:03d}"
                    shot_frames = [f for f in extracted_frames if sd.start_us <= f.actual_us < sd.end_us]
                    shot_frame_paths = [f.path for f in shot_frames]
                    shot_frame_times = [f.actual_us / 1_000_000.0 for f in shot_frames]

                    neg = negotiate(job.requested_capabilities, vision_caps, vision_caps.analysis_mode.value)
                    if i == 0:
                        capability_reports = [
                            {
                                "capability": r.capability,
                                "requested": r.requested,
                                "status": r.status,
                                "analysis_mode": r.analysis_mode,
                                "limitations": r.limitations,
                            }
                            for r in neg.reports
                        ]

                    visual_requested = any(c in job.requested_capabilities for c in ["visual_observations", "temporal_events", "camera_analysis", "visible_text"]) or not job.requested_capabilities
                    if visual_requested and shot_frames:
                        context_hints = {"source_prompt": job.source_prompt} if self.settings.vision.include_context_in_analysis and job.source_prompt else None
                        v_req = VisionAnalysisRequest(
                            job_id=job.job_id,
                            shot_id=sid,
                            shot_start_seconds=sd.start_us / 1_000_000.0,
                            shot_end_seconds=sd.end_us / 1_000_000.0,
                            frame_paths=shot_frame_paths,
                            frame_timestamps_seconds=shot_frame_times,
                            requested_capabilities=job.requested_capabilities,
                            context_hints=context_hints,
                        )
                        try:
                            v_resp, attempts = self.retry_executor.execute(lambda: self.ports.vision.analyze(v_req))
                            analyze_attempts = max(analyze_attempts, attempts)
                            validated_resp = validate_response(v_req, v_resp, vision_caps)
                            vision_results.append(validated_resp)
                        except ExtractionError as e:
                            analysis_failed = True
                            if self.settings.vision.allow_partial_results:
                                shot_drafts[i] = ShotDraft(
                                    id=sd.id,
                                    start_us=sd.start_us,
                                    end_us=sd.end_us,
                                    segment_kind=sd.segment_kind,
                                    boundary_method=sd.boundary_method,
                                    boundary_kind=sd.boundary_kind,
                                    analysis_status="failed",
                                )
                                from scene_signal.ports.visual_analysis import VisionAnalysisResponse
                                vision_results.append(VisionAnalysisResponse(shot_summary=None, observations=[], entities=[], events=[]))
                                shot_warnings.append("PROVIDER_PARTIAL")
                            else:
                                raise e
                    else:
                        from scene_signal.ports.visual_analysis import VisionAnalysisResponse
                        vision_results.append(VisionAnalysisResponse(shot_summary=None, observations=[], entities=[], events=[]))

                stage_attempts["analyze"] = analyze_attempts
                completed_at = datetime.now(timezone.utc).isoformat()

                all_warnings = shot_warnings
                for vr in vision_results:
                    if hasattr(vr, "warnings"):
                        all_warnings.extend(vr.warnings)

                provenance = build_provenance(
                    job_id=job.job_id,
                    asset_id=job.asset_id,
                    asset_fingerprint=resolved.fingerprint,
                    contract_version=job.contract_version,
                    schema_version="1.0",
                    extraction_profile=job.extraction_profile,
                    request_hash=req_hash,
                    sampling_strategy_version=sampling_plan.strategy_version,
                    sampling_parameters=sampling_plan.effective_parameters,
                    media_probe={"name": inspection.probe_name, "version": inspection.probe_version},
                    frame_extractor={"name": "ffmpeg", "version": "6.0"},
                    shot_detector={"name": shot_result.method_name if shot_result else "none", "version": shot_result.method_version if shot_result else "1.0"},
                    vision={"provider": vision_caps.provider, "model": vision_caps.model, "adapter_version": vision_caps.adapter_version, "analysis_mode": vision_caps.analysis_mode.value},
                    started_at=started_at,
                    completed_at=completed_at,
                    stage_attempts=stage_attempts,
                    warning_count=len(all_warnings),
                )

                doc = assemble_document(
                    job=job,
                    asset_fingerprint=resolved.fingerprint,
                    checksum_status=resolved.checksum_status,
                    inspection=inspection,
                    shot_drafts=shot_drafts,
                    extracted_frames=extracted_frames,
                    vision_results=vision_results,
                    capability_reports=capability_reports,
                    warnings=[{"code": w, "message": w, "stage": "pipeline", "severity": "warning"} for w in all_warnings],
                    provenance=provenance,
                )

                # Set outcome = partial if analysis failed partially
                if analysis_failed:
                    doc = doc.model_copy(update={"outcome": "partial"})

                assert_valid_document(doc)

                job_res = JobResult(
                    job_id=job.job_id,
                    status="partial" if analysis_failed else "succeeded",
                    document=doc,
                )

                if self.ports.repository:
                    self.ports.repository.save_result(job.job_id, job_res)
                    self.ports.repository.save_status(
                        job.job_id,
                        JobStatusRecord(
                            job_id=job.job_id,
                            request_hash=req_hash,
                            status="partial" if analysis_failed else "succeeded",
                            current_stage="completed",
                            attempt=1,
                            created_at=started_at,
                            updated_at=completed_at,
                        ),
                    )

                return job_res

        except ExtractionError as e:
            job_res = JobResult(
                job_id=job.job_id,
                status="failed",
                error={
                    "code": e.code.value if hasattr(e.code, "value") else str(e.code),
                    "message": e.message,
                    "retryable": e.retryable,
                    "stage": e.stage,
                    "attempts": stage_attempts.get(e.stage, 1),
                    "details": e.details,
                },
            )
            if self.ports.repository:
                self.ports.repository.save_result(job.job_id, job_res)
                self.ports.repository.save_status(
                    job.job_id,
                    JobStatusRecord(
                        job_id=job.job_id,
                        request_hash=req_hash,
                        status="failed",
                        current_stage=e.stage,
                        attempt=stage_attempts.get(e.stage, 1),
                        created_at=started_at,
                        updated_at=datetime.now(timezone.utc).isoformat(),
                        error=job_res.error,
                    ),
                )
            return job_res
        except Exception as e:
            job_res = JobResult(
                job_id=job.job_id,
                status="failed",
                error={
                    "code": "INTERNAL_ERROR",
                    "message": str(e),
                    "retryable": False,
                    "stage": "pipeline",
                    "attempts": 1,
                    "details": {},
                },
            )
            if self.ports.repository:
                self.ports.repository.save_result(job.job_id, job_res)
            return job_res
