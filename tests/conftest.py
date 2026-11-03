"""Pytest configuration and automatic ffmpeg requirement skipping."""

import shutil

import pytest


def pytest_collection_modifyitems(config, items):
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return
    skip_ffmpeg = pytest.mark.skip(reason="ffmpeg/ffprobe not found on PATH")
    for item in items:
        if "requires_ffmpeg" in item.keywords:
            item.add_marker(skip_ffmpeg)
