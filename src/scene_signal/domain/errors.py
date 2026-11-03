"""Typed errors and error codes for SceneSignal."""

from enum import Enum
from typing import Any, Dict, Optional


class ErrorCode(str, Enum):
    INVALID_JOB_CONTRACT = "INVALID_JOB_CONTRACT"
    UNSUPPORTED_CONTRACT_VERSION = "UNSUPPORTED_CONTRACT_VERSION"
    JOB_ID_CONFLICT = "JOB_ID_CONFLICT"
    JOB_IN_PROGRESS = "JOB_IN_PROGRESS"
    ASSET_SCHEME_UNSUPPORTED = "ASSET_SCHEME_UNSUPPORTED"
    ASSET_NOT_FOUND = "ASSET_NOT_FOUND"
    ASSET_ACCESS_DENIED = "ASSET_ACCESS_DENIED"
    CHECKSUM_MISMATCH = "CHECKSUM_MISMATCH"
    MEDIA_INVALID_OR_CORRUPT = "MEDIA_INVALID_OR_CORRUPT"
    MEDIA_UNSUPPORTED_FORMAT = "MEDIA_UNSUPPORTED_FORMAT"
    MEDIA_NO_VIDEO_STREAM = "MEDIA_NO_VIDEO_STREAM"
    MEDIA_LIMIT_EXCEEDED = "MEDIA_LIMIT_EXCEEDED"
    MEDIA_INSPECTION_FAILED = "MEDIA_INSPECTION_FAILED"
    FRAME_EXTRACTION_FAILED = "FRAME_EXTRACTION_FAILED"
    SHOT_DETECTION_FAILED = "SHOT_DETECTION_FAILED"
    PROVIDER_TIMEOUT = "PROVIDER_TIMEOUT"
    PROVIDER_RATE_LIMITED = "PROVIDER_RATE_LIMITED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PROVIDER_RESPONSE_INVALID = "PROVIDER_RESPONSE_INVALID"
    PROVIDER_CONFIGURATION_ERROR = "PROVIDER_CONFIGURATION_ERROR"
    OUTPUT_VALIDATION_FAILED = "OUTPUT_VALIDATION_FAILED"
    PERSISTENCE_FAILED = "PERSISTENCE_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ExtractionError(Exception):
    """Base exception for SceneSignal errors."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        retryable: bool = False,
        stage: str = "initialization",
        details: Optional[Dict[str, Any]] = None,
        retry_after_seconds: Optional[float] = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.stage = stage
        self.details = details or {}
        self.retry_after_seconds = retry_after_seconds

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code.value if isinstance(self.code, ErrorCode) else self.code,
            "message": self.message,
            "retryable": self.retryable,
            "stage": self.stage,
            "details": self.details,
        }


class InvalidJobContractError(ExtractionError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code=ErrorCode.INVALID_JOB_CONTRACT,
            message=message,
            retryable=False,
            stage="contract_validation",
            details=details,
        )


class UnsupportedContractVersionError(ExtractionError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code=ErrorCode.UNSUPPORTED_CONTRACT_VERSION,
            message=message,
            retryable=False,
            stage="contract_validation",
            details=details,
        )
