"""Server-streamed UI tests (approach #5).

Covers the component-tree builders and the SSE stream with a faked tool call.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

from fastapi.testclient import TestClient

import agentic_ui_demo.routers.rsc as rsc_module
from agentic_ui_demo.config import get_settings
from agentic_ui_demo.routers.rsc import (
    build_delays_overview,
    build_flight_detail,
    build_flight_list,
    build_summary,
)


def test_build_flight_list_filters() -> None:
    nodes = build_flight_list(origin="Graz", destination="Hamburg")
    cards = [n for n in nodes if n["comp"] == "flightCard"]
    assert len(cards) == 3  # AB123, AB124, AB125
    assert nodes[0]["comp"] == "stack" and nodes[0]["parent"] is None
    assert nodes[1]["comp"] == "heading"
    # all cards hang off the root stack
    assert all(c["parent"] == nodes[0]["id"] for c in cards)


def test_build_flight_detail_unknown() -> None:
    nodes = build_flight_detail(flight_id="ZZ999")
    assert any(n["comp"] == "heading" and "not found" in n["props"]["text"] for n in nodes)


def test_build_delays_overview_has_table() -> None:
    nodes = build_delays_overview()
    table = next(n for n in nodes if n["comp"] == "table")
    assert table["props"]["columns"][0] == "Destination"
    assert len(table["props"]["rows"]) >= 1


def test_build_summary_has_three_stats() -> None:
    nodes = build_summary()
    stats = [n for n in nodes if n["comp"] == "stat"]
    assert len(stats) == 3


def _fake_openai(*tool_calls: tuple[str, dict]):
    calls = [
        SimpleNamespace(function=SimpleNamespace(name=name, arguments=json.dumps(args)))
        for name, args in tool_calls
    ]

    class _Completions:
        async def create(self, **_kwargs):
            message = SimpleNamespace(content=None, tool_calls=calls)
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


def test_stream_emits_tool_then_nodes(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    get_settings.cache_clear()
    monkeypatch.setattr(
        rsc_module,
        "AsyncOpenAI",
        _fake_openai(("render_flight_list", {"origin": "Graz", "destination": "Hamburg"})),
    )
    try:
        resp = client.post("/api/rsc/stream", json={"prompt": "flights Graz to Hamburg"})
        assert resp.status_code == 200
        events = _events(resp.text)
    finally:
        get_settings.cache_clear()

    assert events[0]["type"] == "tool" and events[0]["name"] == "render_flight_list"
    node_events = [e for e in events if e["type"] == "node"]
    assert any(e["comp"] == "flightCard" for e in node_events)
    assert events[-1]["type"] == "done"


def test_stream_composes_multiple_tools(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    get_settings.cache_clear()
    monkeypatch.setattr(
        rsc_module,
        "AsyncOpenAI",
        _fake_openai(
            ("render_summary", {}),
            ("render_flight_list", {"only_delayed": True}),
        ),
    )
    try:
        resp = client.post("/api/rsc/stream", json={"prompt": "overview of delays"})
        events = _events(resp.text)
    finally:
        get_settings.cache_clear()

    tool_events = [e for e in events if e["type"] == "tool"]
    assert [t["name"] for t in tool_events] == ["render_summary", "render_flight_list"]
    node_ids = [e["id"] for e in events if e["type"] == "node"]
    assert len(node_ids) == len(set(node_ids))  # ids unique across sections
    assert any(nid.startswith("t0_") for nid in node_ids)
    assert any(nid.startswith("t1_") for nid in node_ids)


def test_stream_requires_key(client: TestClient, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()
    try:
        resp = client.post("/api/rsc/stream", json={"prompt": "hi"})
        assert resp.status_code == 503
    finally:
        get_settings.cache_clear()
