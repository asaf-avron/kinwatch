from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def hmac_key() -> str:
    return "fixture-hmac-key"


@pytest.fixture
def client(tmp_path, monkeypatch, hmac_key):
    monkeypatch.setenv("KINWATCH_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("KINWATCH_USE_FIXTURES", "true")
    monkeypatch.setenv("RING_HMAC_KEY", hmac_key)
    monkeypatch.setenv("KINWATCH_HOST", "0.0.0.0")
    monkeypatch.setenv("KINWATCH_PORT", "8000")
    os.environ["KINWATCH_DATA_DIR"] = str(tmp_path)
    from kinwatch.app import app

    with TestClient(app) as test_client:
        yield test_client
