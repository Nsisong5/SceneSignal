"""Local filesystem asset storage adapter."""

import hashlib
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse, unquote

from scene_signal.domain.errors import ErrorCode, ExtractionError
from scene_signal.ports.asset_storage import AssetStoragePort, ResolvedAsset
from scene_signal.schemas.job import AssetRef


class LocalFilesystemStorageAdapter(AssetStoragePort):
    def __init__(self, max_file_size_bytes: int = 10 * 1024 * 1024 * 1024):
        self.max_file_size_bytes = max_file_size_bytes

    def resolve(self, asset_ref: AssetRef, allowed_roots: List[Path]) -> ResolvedAsset:
        if asset_ref.scheme != "file":
            raise ExtractionError(
                code=ErrorCode.ASSET_SCHEME_UNSUPPORTED,
                message=f"Unsupported asset scheme '{asset_ref.scheme}'. Only 'file' is supported.",
                retryable=False,
                stage="asset_resolution",
            )

        # Parse URI or path
        uri = asset_ref.uri
        if uri.startswith("file://"):
            parsed = urlparse(uri)
            path_str = unquote(parsed.path)
            # Handle windows drive letter in file:///C:/...
            if path_str.startswith("/") and len(path_str) > 2 and path_str[2] == ":":
                path_str = path_str[1:]
            candidate = Path(path_str)
        else:
            candidate = Path(uri)

        # If candidate is relative, resolve against first allowed root if available
        resolved_path: Optional[Path] = None
        if not candidate.is_absolute():
            if allowed_roots:
                resolved_path = (allowed_roots[0] / candidate).resolve()
            else:
                resolved_path = candidate.resolve()
        else:
            resolved_path = candidate.resolve()

        # Check allowed roots containment using realpath
        if allowed_roots:
            allowed_realroots = [r.resolve() for r in allowed_roots]
            is_allowed = False
            try:
                real_target = resolved_path.resolve(strict=True)
            except Exception:
                raise ExtractionError(
                    code=ErrorCode.ASSET_NOT_FOUND,
                    message=f"Asset file not found: {resolved_path}",
                    retryable=False,
                    stage="asset_resolution",
                )

            for root in allowed_realroots:
                try:
                    real_target.relative_to(root)
                    is_allowed = True
                    break
                except ValueError:
                    continue

            if not is_allowed:
                raise ExtractionError(
                    code=ErrorCode.ASSET_ACCESS_DENIED,
                    message=f"Asset path '{real_target}' is outside allowed roots",
                    retryable=False,
                    stage="asset_resolution",
                )
        else:
            try:
                real_target = resolved_path.resolve(strict=True)
            except Exception:
                raise ExtractionError(
                    code=ErrorCode.ASSET_NOT_FOUND,
                    message=f"Asset file not found: {resolved_path}",
                    retryable=False,
                    stage="asset_resolution",
                )

        if not real_target.exists() or not real_target.is_file():
            raise ExtractionError(
                code=ErrorCode.ASSET_NOT_FOUND,
                message=f"Asset file not found or not a file: {real_target}",
                retryable=False,
                stage="asset_resolution",
            )

        file_size = real_target.stat().st_size
        if file_size > self.max_file_size_bytes:
            raise ExtractionError(
                code=ErrorCode.MEDIA_LIMIT_EXCEEDED,
                message=f"Asset file size {file_size} exceeds maximum allowed {self.max_file_size_bytes} bytes",
                retryable=False,
                stage="asset_resolution",
            )

        # Stream hash sha256
        sha256_hash = hashlib.sha256()
        try:
            with open(real_target, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    sha256_hash.update(chunk)
        except Exception as e:
            raise ExtractionError(
                code=ErrorCode.ASSET_ACCESS_DENIED,
                message=f"Failed to read asset file: {e}",
                retryable=False,
                stage="asset_resolution",
            )

        digest = sha256_hash.hexdigest()
        fingerprint = f"sha256:{digest}"

        checksum_status = "not_supplied"
        if asset_ref.checksum:
            if asset_ref.checksum != fingerprint:
                raise ExtractionError(
                    code=ErrorCode.CHECKSUM_MISMATCH,
                    message=f"Asset checksum mismatch: expected {asset_ref.checksum}, got {fingerprint}",
                    retryable=False,
                    stage="asset_resolution",
                    details={"expected": asset_ref.checksum, "actual": fingerprint},
                )
            checksum_status = "verified"

        return ResolvedAsset(
            path=real_target,
            fingerprint=fingerprint,
            checksum_status=checksum_status,
            file_size_bytes=file_size,
        )
