from pathlib import Path
import hashlib
import shutil
import json
from typing import Any
from scene_signal.render.ports.asset_storage import AssetResolverPort, WorkspacePort, ResolvedAsset
from scene_signal.render.ports.repository import RenderRepositoryPort
from scene_signal.render.contracts.edit_plan import PlanAsset
from scene_signal.render.contracts.render_request import RenderRequest
from scene_signal.render.contracts.render_result import RenderResult
from scene_signal.render.contracts.manifest import RenderManifest
from scene_signal.render.domain.errors import RenderError

class LocalResolvedAsset(ResolvedAsset):
    def __init__(self, asset_id: str, local_path: Path, fingerprint: str, size_bytes: int) -> None:
        self._asset_id = asset_id
        self._local_path = local_path
        self._fingerprint = fingerprint
        self._size_bytes = size_bytes

    @property
    def asset_id(self) -> str:
        return self._asset_id

    @property
    def local_path(self) -> Path:
        return self._local_path

    @property
    def fingerprint(self) -> str:
        return self._fingerprint

    @property
    def size_bytes(self) -> int:
        return self._size_bytes

class LocalAssetResolver(AssetResolverPort):
    def __init__(self, assets_root: Path) -> None:
        self.assets_root = assets_root

    def resolve(self, asset: PlanAsset) -> ResolvedAsset:
        uri = asset.asset_ref.uri
        # If uri is absolute or relative
        path = Path(uri)
        if not path.is_absolute():
            path = self.assets_root / uri

        if not path.exists():
            raise RenderError("ASSET_NOT_FOUND", f"Asset file not found: {path}", retryable=False, phase="inspect")

        data = path.read_bytes()
        fp = f"sha256:{hashlib.sha256(data).hexdigest()}"

        if asset.asset_ref.checksum and asset.asset_ref.checksum != fp:
            raise RenderError("ASSET_CHECKSUM_MISMATCH", f"Checksum mismatch for asset {asset.asset_id}", retryable=False, phase="inspect")

        return LocalResolvedAsset(asset.asset_id, path, fp, len(data))

class LocalWorkspace(WorkspacePort):
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self._work_dir = base_dir / "work"
        self._work_dir.mkdir(parents=True, exist_ok=True)

    @property
    def work_dir(self) -> Path:
        return self._work_dir

    def cleanup(self) -> None:
        if self._work_dir.exists():
            shutil.rmtree(self._work_dir, ignore_errors=True)

    def __enter__(self) -> "WorkspacePort":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cleanup()

class LocalRenderRepository(RenderRepositoryPort):
    def __init__(self, data_root: Path) -> None:
        self.data_root = data_root
        self.renders_dir = data_root / "renders"
        self.renders_dir.mkdir(parents=True, exist_ok=True)

    def _job_dir(self, job_id: str) -> Path:
        return self.renders_dir / job_id

    def claim_job(self, render_job_id: str, request_hash: str) -> str:
        job_dir = self._job_dir(render_job_id)
        status_path = job_dir / "status.json"
        req_hash_path = job_dir / "request_hash.txt"

        if not job_dir.exists():
            job_dir.mkdir(parents=True, exist_ok=True)
            req_hash_path.write_text(request_hash, encoding="utf-8")
            status_path.write_text(json.dumps({"status": "claimed"}), encoding="utf-8")
            return "claimed"

        existing_hash = req_hash_path.read_text(encoding="utf-8").strip() if req_hash_path.exists() else ""
        if existing_hash != request_hash:
            return "conflict"

        status_data = json.loads(status_path.read_text(encoding="utf-8")) if status_path.exists() else {"status": "claimed"}
        status = status_data.get("status", "claimed")

        if status == "succeeded":
            return "idempotent_succeeded"
        elif status in ("claimed", "running"):
            return "in_progress"
        return "claimed"

    def save_request(self, render_job_id: str, request: RenderRequest) -> None:
        job_dir = self._job_dir(render_job_id)
        job_dir.mkdir(parents=True, exist_ok=True)
        (job_dir / "request.json").write_text(json.dumps(request.model_dump(mode="json"), indent=2), encoding="utf-8")

    def save_result(self, render_job_id: str, result: RenderResult) -> None:
        job_dir = self._job_dir(render_job_id)
        job_dir.mkdir(parents=True, exist_ok=True)
        (job_dir / "result.json").write_text(json.dumps(result.model_dump(mode="json"), indent=2), encoding="utf-8")
        (job_dir / "status.json").write_text(json.dumps({"status": result.status}), encoding="utf-8")

        # If succeeded, copy output.mp4 from workspace or output path if located in job_dir
        if result.status == "succeeded" and result.output:
            src_out = self.data_root / "work" / "output.mp4" # or similar
            # If result output uri points to somewhere, ensure artifact exists
            pass

    def save_manifest(self, render_job_id: str, manifest: RenderManifest) -> None:
        job_dir = self._job_dir(render_job_id)
        job_dir.mkdir(parents=True, exist_ok=True)
        (job_dir / "manifest.json").write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")

    def load_result(self, render_job_id: str) -> RenderResult | None:
        job_dir = self._job_dir(render_job_id)
        result_path = job_dir / "result.json"
        if result_path.exists():
            try:
                return RenderResult.model_validate_json(result_path.read_text(encoding="utf-8"))
            except Exception:
                return None
        return None

    def get_status(self, render_job_id: str) -> str | None:
        job_dir = self._job_dir(render_job_id)
        status_path = job_dir / "status.json"
        if status_path.exists():
            try:
                data = json.loads(status_path.read_text(encoding="utf-8"))
                return data.get("status")
            except Exception:
                return None
        return None
