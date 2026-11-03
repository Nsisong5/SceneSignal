"""Optional FastAPI application for SceneSignal."""

import shutil
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse

try:
    from fastapi import FastAPI
except ImportError:
    FastAPI = None  # type: ignore

from scene_signal.domain.policies import Settings
from scene_signal.domain.errors import ExtractionError, ErrorCode
from scene_signal.schemas.job import ExtractionJob, parse_extraction_job
from scene_signal.schemas.result import JobResult, JobStatusRecord
from scene_signal.application.service import SceneIntelligenceService
from scene_signal.application.pipeline import PipelinePorts
from scene_signal.adapters.storage.local_fs import LocalFilesystemStorageAdapter
from scene_signal.adapters.media.ffprobe import FFprobeAdapter
from scene_signal.adapters.media.ffmpeg_frames import FFmpegFrameExtractionAdapter
from scene_signal.adapters.media.ffmpeg_shots import FFmpegShotDetectionAdapter
from scene_signal.adapters.fakes.fake_vision import FakeVisionAdapter
from scene_signal.adapters.storage.local_repository import LocalJobRepositoryAdapter


def create_app(service: Optional[SceneIntelligenceService] = None, settings: Optional[Settings] = None) -> FastAPI:
    if FastAPI is None:
        raise RuntimeError("FastAPI is not installed. Install with pip install 'scene-signal[api]'")

    app = FastAPI(title="SceneSignal API", version="0.1.0")
    s = settings or Settings.load()

    # Default service if none provided
    if service is None:
        data_root = Path(".scene_signal/data")
        repo = LocalJobRepositoryAdapter(data_root)
        ports = PipelinePorts(
            storage=LocalFilesystemStorageAdapter(),
            media_probe=FFprobeAdapter(),
            frame_extraction=FFmpegFrameExtractionAdapter(),
            shot_detection=FFmpegShotDetectionAdapter(),
            vision=FakeVisionAdapter(),
            repository=repo,
        )
        service = SceneIntelligenceService(ports=ports, allowed_roots=[Path.cwd()])

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    @app.post("/v1/extractions", response_model=JobResult)
    def create_extraction(job_data: dict, response: Response):
        try:
            job = parse_extraction_job(job_data)
            result = service.extract(job)
            if result.status == "failed":
                err = result.error
                code = err.get("code") if isinstance(err, dict) else getattr(err, "code", "INTERNAL_ERROR")
                raise ExtractionError(code=code, message=err.get("message", "Extraction failed") if isinstance(err, dict) else getattr(err, "message", "Failed"), retryable=err.get("retryable", False) if isinstance(err, dict) else getattr(err, "retryable", False), stage=err.get("stage", "pipeline") if isinstance(err, dict) else getattr(err, "stage", "pipeline"))
            return result
        except ExtractionError as e:
            code = e.code.value if hasattr(e.code, "value") else str(e.code)
            status_code = 500
            if code in ("INVALID_JOB_CONTRACT", "UNSUPPORTED_CONTRACT_VERSION", "MEDIA_LIMIT_EXCEEDED"):
                status_code = 422
            elif code == "ASSET_NOT_FOUND":
                status_code = 404
            elif code == "ASSET_ACCESS_DENIED":
                status_code = 403
            elif code in ("JOB_ID_CONFLICT", "JOB_IN_PROGRESS"):
                status_code = 409
            elif code in ("MEDIA_INVALID_OR_CORRUPT", "MEDIA_UNSUPPORTED_FORMAT"):
                status_code = 415
            elif code in ("PROVIDER_TIMEOUT", "PROVIDER_RATE_LIMITED", "PROVIDER_UNAVAILABLE"):
                status_code = 503
                if e.retry_after_seconds:
                    response.headers["Retry-After"] = str(int(e.retry_after_seconds))

            error_info = {
                "code": code,
                "message": e.message,
                "retryable": e.retryable,
                "stage": e.stage,
                "attempts": 1,
                "details": e.details,
            }
            return JSONResponse(status_code=status_code, content=error_info)
        except Exception as e:
            return JSONResponse(status_code=500, content={"code": "INTERNAL_ERROR", "message": str(e), "retryable": False, "stage": "api", "attempts": 1, "details": {}})

    @app.get("/v1/extractions/{job_id}")
    def get_job_status(job_id: str, data_root: Optional[Path] = None):
        dr = data_root or Path(".scene_signal/data")
        repo = LocalJobRepositoryAdapter(dr)
        st = repo.load_status(job_id)
        if not st:
            raise HTTPException(status_code=404, detail="Job not found")
        return st

    @app.get("/v1/extractions/{job_id}/result", response_model=JobResult)
    def get_job_result(job_id: str, data_root: Optional[Path] = None):
        dr = data_root or Path(".scene_signal/data")
        repo = LocalJobRepositoryAdapter(dr)
        res = repo.load_result(job_id)
        if not res:
            raise HTTPException(status_code=404, detail="Job result not found")
        return res

    return app
