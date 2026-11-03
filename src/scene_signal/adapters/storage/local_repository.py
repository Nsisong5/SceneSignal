"""Local filesystem job repository adapter implementing layout D-05 and atomic writes."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from scene_signal.domain.errors import ErrorCode, ExtractionError
from scene_signal.ports.repository import JobRepositoryPort
from scene_signal.schemas.job import ExtractionJob
from scene_signal.schemas.result import JobResult, JobStatusRecord


class LocalJobRepositoryAdapter(JobRepositoryPort):
    def __init__(self, data_root: Path):
        self.data_root = data_root / "jobs"
        self.data_root.mkdir(parents=True, exist_ok=True)

    def _job_dir(self, job_id: str) -> Path:
        return self.data_root / job_id

    def claim_job(self, job: ExtractionJob, request_hash: str) -> str:
        job_dir = self._job_dir(job.job_id)
        status_path = job_dir / "status.json"
        job_json_path = job_dir / "job.json"

        try:
            job_dir.mkdir(parents=False, exist_ok=False)
        except FileExistsError:
            # Job directory already exists -> check existing job.json and status
            if job_json_path.exists():
                try:
                    existing_data = json.loads(job_json_path.read_text(encoding="utf-8"))
                    existing_hash = existing_data.get("request_hash")
                    # Compare request hash or job parameters
                    existing_job = ExtractionJob.model_validate(existing_data.get("job", {}))
                    # Compute hash excluding correlation_id
                    from scene_signal.domain.canonical import request_hash as compute_hash
                    if compute_hash(existing_job) != request_hash:
                        raise ExtractionError(
                            code=ErrorCode.JOB_ID_CONFLICT,
                            message=f"Job ID '{job.job_id}' already exists with different request parameters",
                            retryable=False,
                            stage="contract_validation",
                            details={"job_id": job.job_id},
                        )
                except ExtractionError:
                    raise
                except Exception:
                    pass

            status_record = self.load_status(job.job_id)
            if status_record:
                if status_record.status in ("succeeded", "partial"):
                    return "idempotent_hit"
                elif status_record.status == "running":
                    raise ExtractionError(
                        code=ErrorCode.JOB_IN_PROGRESS,
                        message=f"Job '{job.job_id}' is currently in progress",
                        retryable=False,
                        stage="pipeline",
                    )
                elif status_record.status == "failed":
                    # Allow re-execution or rerun
                    return "retry_failed"
            return "new"

        # Newly created job directory
        now = datetime.now(timezone.utc).isoformat()
        job_record = {
            "request_hash": request_hash,
            "job": job.model_dump(mode="json"),
        }
        job_json_path.write_text(json.dumps(job_record, indent=2), encoding="utf-8")

        status_record = JobStatusRecord(
            job_id=job.job_id,
            request_hash=request_hash,
            status="pending",
            current_stage="initialization",
            attempt=1,
            created_at=now,
            updated_at=now,
        )
        self.save_status(job.job_id, status_record)
        return "new"

    def save_status(self, job_id: str, status_record: JobStatusRecord) -> None:
        job_dir = self._job_dir(job_id)
        job_dir.mkdir(parents=True, exist_ok=True)
        path = job_dir / "status.json"
        tmp_path = job_dir / "status.json.tmp"
        tmp_path.write_text(json.dumps(status_record.model_dump(mode="json"), indent=2), encoding="utf-8")
        tmp_path.replace(path)

    def load_status(self, job_id: str) -> Optional[JobStatusRecord]:
        path = self._job_dir(job_id) / "status.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return JobStatusRecord.model_validate(data)
        except Exception:
            return None

    def save_result(self, job_id: str, result: JobResult) -> None:
        job_dir = self._job_dir(job_id)
        job_dir.mkdir(parents=True, exist_ok=True)
        path = job_dir / "result.json"
        tmp_path = job_dir / "result.json.tmp"
        tmp_path.write_text(json.dumps(result.model_dump(mode="json"), indent=2), encoding="utf-8")
        tmp_path.replace(path)

    def load_result(self, job_id: str) -> Optional[JobResult]:
        path = self._job_dir(job_id) / "result.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return JobResult.model_validate(data)
        except Exception:
            return None
