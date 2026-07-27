"""Shared test fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from agentic_ui_demo.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
