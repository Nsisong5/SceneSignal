"""Unit tests for FastAPI application."""

import pytest
try:
    from fastapi.testclient import TestClient
    from scene_signal.api.app import create_app
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


@pytest.mark.skipif(not HAS_FASTAPI, reason="FastAPI not installed")
def test_healthz():
    app = create_app()
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
