"""Retry executor with exponential backoff, jitter, and retry-after support."""

import random
import time
from typing import Callable, Optional, TypeVar
from scene_signal.domain.errors import ExtractionError


T = TypeVar("T")


class RetryExecutor:
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay_seconds: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay_seconds: float = 30.0,
        sleeper: Callable[[float], None] = time.sleep,
        rng: Callable[[], float] = random.random,
    ):
        self.max_attempts = max_attempts
        self.initial_delay_seconds = initial_delay_seconds
        self.backoff_factor = backoff_factor
        self.max_delay_seconds = max_delay_seconds
        self.sleeper = sleeper
        self.rng = rng

    def execute(self, func: Callable[[], T], on_retry: Optional[Callable[[Exception, int], None]] = None) -> tuple[T, int]:
        attempts = 0
        delay = self.initial_delay_seconds

        while True:
            attempts += 1
            try:
                result = func()
                return result, attempts
            except ExtractionError as e:
                if not e.retryable or attempts >= self.max_attempts:
                    raise e

                if on_retry:
                    on_retry(e, attempts)

                sleep_time = e.retry_after_seconds if e.retry_after_seconds is not None else delay
                # Full jitter
                jittered_sleep = self.rng() * sleep_time
                actual_sleep = min(self.max_delay_seconds, jittered_sleep)
                self.sleeper(actual_sleep)

                delay *= self.backoff_factor
            except Exception as e:
                # Non-ExtractionError is permanent/non-retryable
                raise e
