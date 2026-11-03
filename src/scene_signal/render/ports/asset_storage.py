from abc import ABC, abstractmethod
from pathlib import Path
from contextlib import AbstractContextManager
from scene_signal.render.contracts.edit_plan import PlanAsset, AssetRef

class ResolvedAsset(ABC):
    @property
    @abstractmethod
    def asset_id(self) -> str:
        pass

    @property
    @abstractmethod
    def local_path(self) -> Path:
        pass

    @property
    @abstractmethod
    def fingerprint(self) -> str:
        pass

    @property
    @abstractmethod
    def size_bytes(self) -> int:
        pass

class AssetResolverPort(ABC):
    @abstractmethod
    def resolve(self, asset: PlanAsset) -> ResolvedAsset:
        pass

class WorkspacePort(AbstractContextManager["WorkspacePort"], ABC):
    @property
    @abstractmethod
    def work_dir(self) -> Path:
        pass

    @abstractmethod
    def cleanup(self) -> None:
        pass
