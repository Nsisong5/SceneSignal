"""Asset storage port and workspace definitions."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
from scene_signal.schemas.job import AssetRef


@dataclass(frozen=True)
class ResolvedAsset:
    path: Path
    fingerprint: str
    checksum_status: str
    file_size_bytes: int


class Workspace:
    """Manages temporary working directories for job artifacts."""

    def __init__(self, job_id: str, work_root: Optional[Path] = None, keep_artifacts: bool = False):
        self.job_id = job_id
        self.work_root = work_root or (Path.cwd() / ".scene_signal" / "work")
        self.keep_artifacts = keep_artifacts
        self.path = self.work_root / job_id

    def __enter__(self) -> "Workspace":
        self.path.mkdir(parents=True, exist_ok=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if not self.keep_artifacts and self.path.exists():
            import shutil
            shutil.rmtree(self.path, ignore_errors=True)

    def sub_dir(self, name: str) -> Path:
        d = self.path / name
        d.mkdir(parents=True, exist_ok=True)
        return d


class AssetStoragePort(ABC):
    @abstractmethod
    def resolve(self, asset_ref: AssetRef, allowed_roots: List[Path]) -> ResolvedAsset:
        """Resolve AssetRef to a local file, verify checksum, and compute fingerprint."""
        pass
