from abc import ABC, abstractmethod
from typing import Any
from scene_signal.render.contracts.render_request import RenderRequest
from scene_signal.render.contracts.render_result import RenderResult
from scene_signal.render.contracts.manifest import RenderManifest

class RenderRepositoryPort(ABC):
    @abstractmethod
    def claim_job(self, render_job_id: str, request_hash: str) -> str:
        """Claim a job atomically. Returns status: 'claimed', 'idempotent_succeeded', 'in_progress', 'conflict'."""
        pass

    @abstractmethod
    def save_request(self, render_job_id: str, request: RenderRequest) -> None:
        pass

    @abstractmethod
    def save_result(self, render_job_id: str, result: RenderResult) -> None:
        pass

    @abstractmethod
    def save_manifest(self, render_job_id: str, manifest: RenderManifest) -> None:
        pass

    @abstractmethod
    def load_result(self, render_job_id: str) -> RenderResult | None:
        pass

    @abstractmethod
    def get_status(self, render_job_id: str) -> str | None:
        pass
