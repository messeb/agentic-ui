"""Protocol-decoupled (AG-UI / MCP-UI) tests — approach #8.

The event stream is deterministic given the resolved intent; we fake the OpenAI intent call and
assert the emitted AG-UI event sequence, the JSON Patch STATE_DELTA, and the MCP-UI resource.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

from fastapi.testclient import TestClient

import agentic_ui_demo.routers.protocol as proto_module
from agentic_ui_demo.config import get_settings
from agentic_ui_demo.routers.protocol import EVENT_TYPES


def test_info_lists_protocols_and_16_event_types(client: TestClient) -> None:
    resp = client.get("/api/protocol/info")
    assert resp.status_code == 200
    body = resp.json()
    assert {p["name"] for p in body["protocols"]} == {"MCP", "MCP-UI", "AG-UI"}
    total = sum(len(v) for v in EVENT_TYPES.values())
    assert total == 16


def _fake_openai(intent: dict):
    class _Completions:
        async def create(self, **_kwargs):
            message = SimpleNamespace(content=json.dumps(intent))
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    class _Client:
        def __init__(self, **_kwargs):
            self.chat = SimpleNamespace(completions=_Completions())

    return _Client


def _events(text: str) -> list[dict]:
    out = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            data = line[5:].strip()
            if data and data != "[DONE]":
                out.append(json.loads(data))
    return out


def _run(client: TestClient, monkeypatch, intent: dict) -> list[dict]:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    get_settings.cache_clear()
    monkeypatch.setattr(proto_module, "AsyncOpenAI", _fake_openai(intent))
    try:
        resp = client.post("/api/protocol/run", json={"prompt": "x"})
        assert resp.status_code == 200
        return _events(resp.text)
    finally:
        get_settings.cache_clear()


def test_search_run_emits_lifecycle_and_snapshot(client: TestClient, monkeypatch) -> None:
    events = _run(
        client,
        monkeypatch,
        {
            "action": "search",
            "origin": "Graz",
            "destination": "Hamburg",
            "flight_id": None,
            "message": "Found flights.",
        },
    )
    types = [e["type"] for e in events]
    assert types[0] == "RUN_STARTED"
    assert types[-1] == "RUN_FINISHED"
    assert "TOOL_CALL_START" in types and "TOOL_CALL_RESULT" in types
    assert "STATE_SNAPSHOT" in types
    assert "TEXT_MESSAGE_CONTENT" in types
    snapshot = next(e for e in events if e["type"] == "STATE_SNAPSHOT")["snapshot"]
    assert len(snapshot["flights"]) == 3  # AB123, AB124, AB125


def test_book_run_emits_state_delta_json_patch(client: TestClient, monkeypatch) -> None:
    events = _run(
        client,
        monkeypatch,
        {
            "action": "book",
            "origin": None,
            "destination": None,
            "flight_id": "AB123",
            "message": "Booked.",
        },
    )
    delta = next(e for e in events if e["type"] == "STATE_DELTA")["delta"]
    assert delta[0]["op"] == "add"
    assert delta[0]["path"] == "/booking"
    assert delta[0]["value"]["flight_id"] == "AB123"


def test_show_run_emits_mcp_ui_resource(client: TestClient, monkeypatch) -> None:
    events = _run(
        client,
        monkeypatch,
        {
            "action": "show",
            "origin": None,
            "destination": None,
            "flight_id": "AB123",
            "message": "Here it is.",
        },
    )
    result = next(e for e in events if e["type"] == "TOOL_CALL_RESULT")
    content = result["content"]
    assert content["type"] == "resource"
    assert content["resource"]["uri"].startswith("ui://flight/")
    assert "<html" in content["resource"]["text"]


def test_run_requires_key(client: TestClient, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()
    try:
        resp = client.post("/api/protocol/run", json={"prompt": "x"})
        assert resp.status_code == 503
    finally:
        get_settings.cache_clear()
