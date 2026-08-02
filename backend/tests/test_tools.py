"""Tool-calling tests (approach #2).

Covers the dispatcher/handlers, the permission gate, and the full agent loop with a faked
OpenAI client — read tools auto-execute, side-effect tools pause for approval, and an approved
resume completes the action. No real API key required.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from agentic_ui_demo.config import get_settings
from agentic_ui_demo.tools import REGISTRY, reset_state
from agentic_ui_demo.tools.flights import book_flight, search_flights


@pytest.fixture(autouse=True)
def _fresh_state():
    reset_state()
    yield
    reset_state()


# --- handlers / dispatcher ---------------------------------------------------


def test_search_flights_filters() -> None:
    out = search_flights("Graz", "Hamburg")
    assert out["count"] == 2
    assert {f["id"] for f in out["flights"]} == {"AB123", "AB124"}


def test_book_flight_decrements_seats() -> None:
    before = REGISTRY["get_flight"].handler(flight_id="AB123")["seats"]
    res = book_flight("AB123", "Alice")
    assert res["booked"] is True
    assert res["seats_left"] == before - 1


def test_book_sold_out_flight_errors() -> None:
    res = book_flight("CD201", "Bob")  # 0 seats
    assert "error" in res


def test_registry_marks_side_effects() -> None:
    assert REGISTRY["book_flight"].side_effect is True
    assert REGISTRY["search_flights"].side_effect is False


# --- fake OpenAI client ------------------------------------------------------


def _tc(cid: str, name: str, args: dict) -> SimpleNamespace:
    return SimpleNamespace(id=cid, function=SimpleNamespace(name=name, arguments=json.dumps(args)))


def _resp(content=None, tool_calls=None) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content, tool_calls=tool_calls))]
    )


def _fake_openai(script):
    class _Completions:
        def __init__(self):
            self._script = list(script)

        async def create(self, **_kwargs):
            return self._script.pop(0)

    class _Client:
        def __init__(self, **_kwargs):
            self.chat = SimpleNamespace(completions=_Completions())

    return _Client


def _events(text: str) -> list[dict]:
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if data and data != "[DONE]":
            out.append(json.loads(data))
    return out


def _use_fake(monkeypatch, script):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    get_settings.cache_clear()
    monkeypatch.setattr("agentic_ui_demo.llm.AsyncOpenAI", _fake_openai(script))


# --- agent loop --------------------------------------------------------------


def test_read_tool_runs_then_final(client: TestClient, monkeypatch) -> None:
    script = [
        _resp(
            tool_calls=[_tc("c1", "search_flights", {"origin": "Graz", "destination": "Hamburg"})]
        ),
        _resp(content="I found 2 flights."),
    ]
    _use_fake(monkeypatch, script)
    try:
        resp = client.post(
            "/api/tools/chat",
            json={"messages": [{"role": "user", "content": "flights Graz to Hamburg"}]},
        )
    finally:
        get_settings.cache_clear()

    events = _events(resp.text)
    kinds = [e["type"] for e in events]
    assert "tool_call" in kinds and "tool_result" in kinds and "final" in kinds
    result = next(e for e in events if e["type"] == "tool_result")["result"]
    assert result["count"] == 2
    assert next(e for e in events if e["type"] == "final")["content"] == "I found 2 flights."


def test_side_effect_pauses_for_permission(client: TestClient, monkeypatch) -> None:
    script = [
        _resp(tool_calls=[_tc("c9", "book_flight", {"flight_id": "AB123", "passenger": "Alice"})])
    ]
    _use_fake(monkeypatch, script)
    try:
        resp = client.post(
            "/api/tools/chat",
            json={"messages": [{"role": "user", "content": "book AB123 for Alice"}]},
        )
    finally:
        get_settings.cache_clear()

    events = _events(resp.text)
    kinds = [e["type"] for e in events]
    assert "awaiting_permission" in kinds
    assert "tool_result" not in kinds  # nothing executed yet
    # seat count unchanged — the booking did not run
    assert REGISTRY["get_flight"].handler(flight_id="AB123")["seats"] == 4


def test_approved_resume_executes_booking(client: TestClient, monkeypatch) -> None:
    script = [_resp(content="Booked! Your confirmation is BK001.")]
    _use_fake(monkeypatch, script)
    pending_assistant = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "id": "c9",
                "type": "function",
                "function": {
                    "name": "book_flight",
                    "arguments": json.dumps({"flight_id": "AB123", "passenger": "Alice"}),
                },
            }
        ],
    }
    try:
        resp = client.post(
            "/api/tools/chat",
            json={
                "messages": [
                    {"role": "user", "content": "book AB123 for Alice"},
                    pending_assistant,
                ],
                "approvals": {"c9": True},
            },
        )
    finally:
        get_settings.cache_clear()

    events = _events(resp.text)
    tool_result = next(e for e in events if e["type"] == "tool_result")
    assert tool_result["result"]["booked"] is True
    assert REGISTRY["get_flight"].handler(flight_id="AB123")["seats"] == 3


def test_denied_resume_does_not_execute(client: TestClient, monkeypatch) -> None:
    script = [_resp(content="No problem, I did not book it.")]
    _use_fake(monkeypatch, script)
    pending_assistant = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "id": "c9",
                "type": "function",
                "function": {
                    "name": "book_flight",
                    "arguments": json.dumps({"flight_id": "AB123", "passenger": "Alice"}),
                },
            }
        ],
    }
    try:
        resp = client.post(
            "/api/tools/chat",
            json={
                "messages": [
                    {"role": "user", "content": "book it"},
                    pending_assistant,
                ],
                "approvals": {"c9": False},
            },
        )
    finally:
        get_settings.cache_clear()

    events = _events(resp.text)
    tool_result = next(e for e in events if e["type"] == "tool_result")
    assert tool_result["denied"] is True
    assert REGISTRY["get_flight"].handler(flight_id="AB123")["seats"] == 4


def test_list_tools_endpoint(client: TestClient) -> None:
    resp = client.get("/api/tools")
    assert resp.status_code == 200
    tools = resp.json()["tools"]
    assert len(tools) == 5
    assert any(t["name"] == "book_flight" and t["side_effect"] for t in tools)


def test_tool_chat_requires_key(client: TestClient, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()
    try:
        resp = client.post(
            "/api/tools/chat", json={"messages": [{"role": "user", "content": "hi"}]}
        )
        assert resp.status_code == 503
    finally:
        get_settings.cache_clear()
