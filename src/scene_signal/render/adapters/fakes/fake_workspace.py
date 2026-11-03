from pathlib import Path
from scene_signal.render.ports.asset_storage import WorkspacePort

class FakeWorkspace(WorkspacePort):
    def __init__(self, work_dir: Path) -> None:
        self._work_dir = work_dir
        self._work_dir.mkdir(parents=True, exist_ok=True)

    @property
    def work_dir(self) -> Path:
        return self._work_dir

    def cleanup(self) -> None:
        pass

    def __enter__(self) -> "WorkspacePort":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cleanup()
