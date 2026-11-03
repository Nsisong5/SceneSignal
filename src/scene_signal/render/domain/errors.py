from typing import Any

from scene_signal.render.contracts.error_info import ErrorInfo


class RenderError(Exception):
    def __init__(self, code: str, message: str, retryable: bool = False, phase: str = "validate", details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.phase = phase
        self.details = details or {}

    def to_error_info(self) -> ErrorInfo:
        return ErrorInfo(
            code=self.code,
            message=self.message,
            retryable=self.retryable,
            phase=self.phase,
            details=self.details
        )
