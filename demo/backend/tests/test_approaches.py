"""Tests for the approaches API and manifest integrity."""

from __future__ import annotations

from fastapi import status
from fastapi.testclient import TestClient

from agentic_ui_demo.registry import list_approaches

EXPECTED_IDS = {
    "conversational-chatbot",
    "tool-calling",
    "component-selection",
    "sandboxed-code",
    "server-streamed-ui",
    "intent-adaptive",
    "agentic-frontend",
    "protocol-decoupled",
}


def test_manifest_has_eight_unique_approaches() -> None:
    approaches = list_approaches()
    assert len(approaches) == 8
    ids = {a.id for a in approaches}
    assert ids == EXPECTED_IDS
    assert {a.number for a in approaches} == set(range(1, 9))


def test_health(client: TestClient) -> None:
    resp = client.get("/api/health")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["status"] == "ok"


def test_list_approaches(client: TestClient) -> None:
    resp = client.get("/api/approaches")
    assert resp.status_code == status.HTTP_200_OK
    assert len(resp.json()) == 8


def test_get_one_approach(client: TestClient) -> None:
    resp = client.get("/api/approaches/tool-calling")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["title"] == "Function / Tool Calling"


def test_get_unknown_approach_404(client: TestClient) -> None:
    resp = client.get("/api/approaches/does-not-exist")
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_every_demo_endpoint_is_stubbed_501(client: TestClient) -> None:
    for approach in list_approaches():
        resp = client.get(f"/api/approaches/{approach.id}/demo")
        assert resp.status_code == status.HTTP_501_NOT_IMPLEMENTED
        assert resp.json()["status"] == "not-implemented"
