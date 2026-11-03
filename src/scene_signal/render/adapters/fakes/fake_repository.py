from pathlib import Path
from scene_signal.render.ports.repository import RenderRepositoryPort
from scene_signal.render.contracts.render_request import RenderRequest
from scene_signal.render.contracts.render_result import RenderResult
from scene_signal.render.contracts.manifest import RenderManifest

class FakeRenderRepository(RenderRepositoryPort):
    def __init__(self) -> None:
        self.jobs: dict[str, dict[str, Any]] = {}

    def claim_job(self, render_job_id: str, request_hash: str) -> str:
        if render_job_id not in self.jobs:
            self.jobs[render_job_id] = {
                "status": "claimed",
                "request_hash": request_hash,
                "result": None,
                "manifest": None,
                "request": None,
            }
            return "claimed"
        
        job = self.jobs[render_job_id]
        if job["request_hash"] != request_hash:
            return "conflict"
        
        status = job["status"]
        if status == "succeeded":
            return "idempotent_succeeded"
        elif status == "running" or status == "claimed":
            return "in_progress"
        return "claimed"

    def save_request(self, render_job_id: str, request: RenderRequest) -> None:
        if render_job_id in self.jobs:
            self.jobs[render_job_id]["request"] = request

    def save_result(self, render_job_id: str, result: RenderResult) -> None:
        if render_job_id in self.jobs:
            self.jobs[render_job_id]["result"] = result
            self.jobs[render_job_id]["status"] = result.status

    def save_manifest(self, render_job_id: str, manifest: RenderManifest) -> None:
        if render_job_id in self.jobs:
            self.jobs[render_job_id]["manifest"] = manifest

    def load_result(self, render_job_id: str) -> RenderResult | None:
        if render_job_id in self.jobs:
            return self.jobs[render_job_id]["result"]
        return None

    def get_status(self, render_job_id: str) -> str | None:
        if render_job_id in self.jobs:
            return self.jobs[render_job_id]["status"]
        return None
