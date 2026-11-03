"""Unit tests for LocalFilesystemStorageAdapter and Workspace."""

from pathlib import Path
import pytest
from scene_signal.adapters.storage.local_fs import LocalFilesystemStorageAdapter
from scene_signal.ports.asset_storage import Workspace
from scene_signal.schemas.job import AssetRef
from scene_signal.domain.errors import ExtractionError


def test_workspace_lifecycle(tmp_path):
    ws_root = tmp_path / "work"
    with Workspace("job-123", work_root=ws_root, keep_artifacts=False) as ws:
        assert ws.path.exists()
        sub = ws.sub_dir("frames")
        assert sub.exists()
    assert not ws.path.exists()

    with Workspace("job-456", work_root=ws_root, keep_artifacts=True) as ws:
        pass
    assert ws.path.exists()


def test_local_storage_resolve_success(tmp_path):
    media = tmp_path / "clip.mp4"
    media.write_bytes(b"some fake video content")

    adapter = LocalFilesystemStorageAdapter()
    ref = AssetRef(scheme="file", uri=str(media))
    resolved = adapter.resolve(ref, [tmp_path])

    assert resolved.path == media.resolve()
    assert resolved.fingerprint.startswith("sha256:")
    assert resolved.checksum_status == "not_supplied"


def test_local_storage_checksum_verified(tmp_path):
    media = tmp_path / "clip.mp4"
    media.write_bytes(b"some fake video content")

    adapter = LocalFilesystemStorageAdapter()
    # Compute actual checksum
    import hashlib
    digest = hashlib.sha256(b"some fake video content").hexdigest()
    checksum = f"sha256:{digest}"

    ref = AssetRef(scheme="file", uri=str(media), checksum=checksum)
    resolved = adapter.resolve(ref, [tmp_path])
    assert resolved.checksum_status == "verified"


def test_local_storage_checksum_mismatch(tmp_path):
    media = tmp_path / "clip.mp4"
    media.write_bytes(b"some fake video content")

    adapter = LocalFilesystemStorageAdapter()
    ref = AssetRef(scheme="file", uri=str(media), checksum="sha256:" + "0" * 64)
    with pytest.raises(ExtractionError) as exc_info:
        adapter.resolve(ref, [tmp_path])
    assert exc_info.value.code.value == "CHECKSUM_MISMATCH"


def test_local_storage_access_denied(tmp_path):
    root1 = tmp_path / "root1"
    root1.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    file_outside = outside / "secret.mp4"
    file_outside.write_bytes(b"data")

    adapter = LocalFilesystemStorageAdapter()
    ref = AssetRef(scheme="file", uri=str(file_outside))
    with pytest.raises(ExtractionError) as exc_info:
        adapter.resolve(ref, [root1])
    assert exc_info.value.code.value == "ASSET_ACCESS_DENIED"


def test_local_storage_unsupported_scheme(tmp_path):
    adapter = LocalFilesystemStorageAdapter()
    ref = AssetRef(scheme="https", uri="https://example.com/video.mp4")
    with pytest.raises(ExtractionError) as exc_info:
        adapter.resolve(ref, [tmp_path])
    assert exc_info.value.code.value == "ASSET_SCHEME_UNSUPPORTED"
