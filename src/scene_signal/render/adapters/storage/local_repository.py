from pathlib import Path
import json
import shutil
import time
from typing import Any
from scene_signal.render.ports.repository import RenderRepositoryPort
from scene_signal.render.contracts.render_request import RenderRequest
from scene_signal.render.contracts.render_result import RenderResult
from scene_signal.render.contracts.manifest import RenderManifest

class LocalRenderRepository(RenderRepositoryPort):
    def __init__(self, data_root: Path) -> None:
        self.data_root = data_root
        self.renders_dir = data_root / "renders"
        self.renders_dir.mkdir(parents=True, exist_ok=True)

    def _job_dir(self, render_job_id: str) -> Path:
        return self.renders_dir / render_job_id

    def claim_job(self, render_job_id: str, request_hash: str) -> str:
        job_dir = self._job_dir(render_job_id)
        status_path = job_dir / "status.json"
        req_hash_path = job_dir / "request_hash.txt"

        if not job_dir.exists():
            job_dir.mkdir(parents=True, exist_ok=True)
            req_hash_path.write_text(request_hash, encoding="utf-8")
            status_path.write_text(json.dumps({"status": "claimed"}, indent=2), encoding="utf-8")
            return "claimed"

        if req_hash_path.exists():
            existing_hash = req_hash_path.read_text(encoding="utf-8").strip()
            if existing_hash != request_hash:
                return "conflict"

        if status_path.exists():
            try:
                st = json.loads(status_path.read_text(encoding="utf-8"))
                status = st.get("status")
                if status == "succeeded":
                    return "idempotent_succeeded"
                elif status in ("claimed", "running"):
                    return "in_progress"
            except Exception:
                pass

        return "claimed"

    def save_request(self, render_job_id: str, request: RenderRequest) -> None:
        job_dir = self._job_dir(render_job_id)
        job_dir.mkdir(parents=True, exist_ok=True)
        (job_dir / "request.json").write_text(json.dumps(request.model_dump(mode="json"), indent=2), encoding="utf-8")

    def save_result(self, render_job_id: str, result: RenderResult) -> None:
        job_dir = self._job_dir(render_job_id)
        job_dir.mkdir(parents=True, exist_ok=True)
        (job_dir / "result.json").write_text(json.dumps(result.model_dump(mode="json"), indent=2), encoding="utf-8")
        (job_dir / "status.json").write_text(json.dumps({"status": result.status}, indent=2), encoding="utf-8")

    def save_manifest(self, render_job_id: str, manifest: RenderManifest) -> None:
        job_dir = self._job_dir(render_job_id)
        job_dir.mkdir(parents=True, exist_ok=True)
        (job_dir / "manifest.json").write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")

    def load_result(self, render_job_id: str) -> RenderResult | None:
        job_dir = self._job_dir(render_job_id)
        res_path = job_dir / "result.json"
        if not res_path.exists():
            return None
        try:
            data = json.loads(res_path.read_text(encoding="utf-8"))
            return RenderResult.model_validate(data)
        except Exception:
            return None

    def get_status(self, render_job_id: str) -> str | None:
        job_dir = self._job_dir(render_job_id)
        status_path = job_dir / "status.json"
        if not status_path.exists():
            return None
        try:
            st = json.loads(status_path.read_text(encoding="utf-8"))
            return st.get("status")
        except Exception:
            return None

    def cleanup_stale(self, older_than_hours: int) -> int:
        count = 0
        now = time.time()
        threshold = older_than_hours * 3600
        work_dir = self.data_root / "work"
        if work_dir.exists():
            for child in work_dir.iterdir():
                if child.is_dir():
                    mtime = child.stat().st_mtime
                    if (now - mtime) > threshold:
                        shutil.rmtree(child, ignore_errors=True)
                        count += 1
        return count
