"""Agentic frontend tests (approach #7).

The backend is stateless: given a goal + live state it returns the next tool calls. Verified with
a faked OpenAI client. Also checks that every tool schema requires the `next` directive.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

from fastapi.testclient import TestClient

import agentic_ui_demo.routers.agent as agent_module
from agentic_ui_demo.config import get_settings
from agentic_ui_demo.routers.agent import TOOLS


def test_every_tool_requires_next() -> None:
    for tool in TOOLS:
        params = tool["function"]["parameters"]
        assert "next" in params["properties"]
        assert "next" in params["required"]


def test_data_endpoint(client: TestClient) -> None:
    resp = client.get("/api/agent/data")
    assert resp.status_code == 200
    assert len(resp.json()["flights"]) == 8


def _fake_openai(*tool_calls: tuple[str, dict]):
    calls = [
        SimpleNamespace(function=SimpleNamespace(name=name, arguments=json.dumps(args)))
        for name, args in tool_calls
    ]

    class _Completions:
        async def create(self, **_kwargs):
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=None, tool_calls=calls))]
            )

    class _Client:
        def __init__(self, **_kwargs):
            self.chat = SimpleNamespace(completions=_Completions())

    return _Client


def test_step_returns_parsed_tool_calls(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    get_settings.cache_clear()
    monkeypatch.setattr(
        agent_module,
        "AsyncOpenAI",
        _fake_openai(
            ("update_form", {"field": "destination", "value": "Hamburg", "next": "continue"}),
            ("goto", {"step": "results", "next": "continue"}),
        ),
    )
    try:
        resp = client.post(
            "/api/agent/step",
            json={"goal": "fly to Hamburg", "state": {"step": "search", "form": {}}},
        )
        assert resp.status_code == 200
        body = resp.json()
    finally:
        get_settings.cache_clear()

    names = [c["name"] for c in body["calls"]]
    assert names == ["update_form", "goto"]
    assert body["calls"][0]["args"]["value"] == "Hamburg"
    assert body["calls"][0]["next"] == "continue"


def test_step_requires_key(client: TestClient, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()
    try:
        resp = client.post("/api/agent/step", json={"goal": "x", "state": {}})
        assert resp.status_code == 503
    finally:
        get_settings.cache_clear()
