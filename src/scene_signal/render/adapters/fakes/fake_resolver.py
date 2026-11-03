from pathlib import Path
import hashlib
from scene_signal.render.ports.asset_storage import AssetResolverPort, ResolvedAsset
from scene_signal.render.contracts.edit_plan import PlanAsset
from scene_signal.render.domain.errors import RenderError

class FakeResolvedAsset(ResolvedAsset):
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

class FakeAssetResolver(AssetResolverPort):
    def __init__(self, assets_root: Path) -> None:
        self.assets_root = assets_root.resolve()

    def resolve(self, asset: PlanAsset) -> ResolvedAsset:
        try:
            path = (self.assets_root / asset.asset_ref.uri).resolve()
            if not path.is_relative_to(self.assets_root):
                raise RenderError(
                    code="ASSET_ACCESS_DENIED",
                    message=f"Asset path traversal denied: {asset.asset_ref.uri}",
                    retryable=False,
                    phase="validate",
                )
        except RenderError:
            raise
        except Exception as e:
            raise RenderError(
                code="ASSET_ACCESS_DENIED",
                message=f"Invalid asset path: {asset.asset_ref.uri}",
                retryable=False,
                phase="validate",
            ) from e

        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"fake video bytes")
        
        data = path.read_bytes()
        fp = f"sha256:{hashlib.sha256(data).hexdigest()}"
        return FakeResolvedAsset(asset.asset_id, path, fp, len(data))
