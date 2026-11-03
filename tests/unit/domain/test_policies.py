"""Unit tests for Settings and policies."""

import pytest

from scene_signal.domain.policies import Settings


def test_settings_load_defaults():
    settings = Settings.load({})
    assert settings.timeout_seconds == 30.0
    assert settings.retry.max_attempts == 3
    assert "standard" in settings.profiles


def test_settings_load_env():
    settings = Settings.load({"SCENE_SIGNAL_MAX_ATTEMPTS": "5", "SCENE_SIGNAL_TIMEOUT_SECONDS": "15.0"})
    assert settings.retry.max_attempts == 5
    assert settings.timeout_seconds == 15.0


def test_settings_validation_errors():
    with pytest.raises(ValueError):
        Settings.load({"SCENE_SIGNAL_MAX_ATTEMPTS": "0"})
    with pytest.raises(ValueError):
        Settings.load({"SCENE_SIGNAL_TIMEOUT_SECONDS": "-1"})
