from typing import Any

from pydantic import BaseModel, ConfigDict


class ErrorInfo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    message: str
    retryable: bool
    phase: str
    details: dict[str, Any] = {}
