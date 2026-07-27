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


def test_unimplemented_demo_endpoints_are_stubbed_501(client: TestClient) -> None:
    unimplemented = [a for a in list_approaches() if a.status == "not-implemented"]
    assert len(unimplemented) == 7  # approach #1 is implemented
    for approach in unimplemented:
        resp = client.get(f"/api/approaches/{approach.id}/demo")
        assert resp.status_code == status.HTTP_501_NOT_IMPLEMENTED
        assert resp.json()["status"] == "not-implemented"


def test_conversational_chatbot_is_implemented(client: TestClient) -> None:
    resp = client.get("/api/approaches/conversational-chatbot")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["status"] == "implemented"


def test_chat_requires_api_key(client: TestClient, monkeypatch) -> None:
    # Force "no key" regardless of the dev's environment → graceful 503, not a crash.
    from agentic_ui_demo.config import get_settings

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()
    try:
        resp = client.post("/api/chat", json={"messages": [{"role": "user", "content": "hi"}]})
        assert resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    finally:
        get_settings.cache_clear()


def test_chat_rejects_empty_messages(client: TestClient) -> None:
    resp = client.post("/api/chat", json={"messages": []})
    assert resp.status_code == 422
