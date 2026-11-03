"""Unit tests for RetryExecutor."""

import pytest
from scene_signal.application.retry import RetryExecutor
from scene_signal.domain.errors import ExtractionError, ErrorCode


class TransientError(ExtractionError):
    def __init__(self):
        super().__init__(code=ErrorCode.PROVIDER_TIMEOUT, message="Timeout", retryable=True, stage="analyze")


class PermanentError(ExtractionError):
    def __init__(self):
        super().__init__(code=ErrorCode.INVALID_JOB_CONTRACT, message="Bad", retryable=False, stage="contract_validation")


def test_retry_success_after_transient():
    attempts = 0

    def flaky():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise TransientError()
        return "success"

    executor = RetryExecutor(max_attempts=3, sleeper=lambda s: None)
    res, count = executor.execute(flaky)
    assert res == "success"
    assert count == 3


def test_retry_exhausted():
    def always_fail():
        raise TransientError()

    executor = RetryExecutor(max_attempts=2, sleeper=lambda s: None)
    with pytest.raises(TransientError):
        executor.execute(always_fail)


def test_permanent_error_no_retry():
    attempts = 0

    def perm():
        nonlocal attempts
        attempts += 1
        raise PermanentError()

    executor = RetryExecutor(max_attempts=3, sleeper=lambda s: None)
    with pytest.raises(PermanentError):
        executor.execute(perm)
    assert attempts == 1
