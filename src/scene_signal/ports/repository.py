"""Job repository port definition."""

from abc import ABC, abstractmethod
from typing import Optional
from scene_signal.schemas.job import ExtractionJob
from scene_signal.schemas.result import JobResult, JobStatusRecord


class JobRepositoryPort(ABC):
    @abstractmethod
    def claim_job(self, job: ExtractionJob, request_hash: str) -> str:
        """Claim job ID atomically. Returns status: 'new', 'idempotent_hit', 'running', or raises conflict."""
        pass

    @abstractmethod
    def save_status(self, job_id: str, status_record: JobStatusRecord) -> None:
        pass

    @abstractmethod
    def load_status(self, job_id: str) -> Optional[JobStatusRecord]:
        pass

    @abstractmethod
    def save_result(self, job_id: str, result: JobResult) -> None:
        pass

    @abstractmethod
    def load_result(self, job_id: str) -> Optional[JobResult]:
        pass
