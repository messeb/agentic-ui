"""Server-streamed UI tests (approach #5).

Covers the server-rendered HTML-fragment builders (flight cards as the <flight-card> web
component) and the SSE stream with a faked tool call.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

from fastapi.testclient import TestClient

from agentic_ui_demo.config import get_settings
from agentic_ui_demo.routers.rsc import (
    build_delays_overview,
    build_flight_detail,
    build_flight_list,
    build_summary,
)


def test_build_flight_list_renders_html_web_components() -> None:
    frags = build_flight_list(origin="Graz", destination="Hamburg")
    # real HTML fragments (a heading) + a <flight-card> web component per flight
    assert frags[0].startswith("<h2")
    cards = [f for f in frags if f.startswith("<flight-card")]
    assert len(cards) == 3  # AB123, AB124, AB125
    assert 'fid="AB123"' in cards[0]
    assert 'route="Graz → Hamburg"' in cards[0]


def test_build_flight_detail_unknown() -> None:
    frags = build_flight_detail(flight_id="ZZ999")
    assert any("Flight not found" in f for f in frags)


def test_build_delays_overview_has_table() -> None:
    frags = build_delays_overview()
    assert any("<table" in f and "Destination" in f for f in frags)


def test_build_summary_has_three_stats() -> None:
    frags = build_summary()
    joined = "".join(frags)
    for label in ("Flights", "Avg price", "On-time"):
        assert label in joined


def test_model_text_is_escaped() -> None:
    # a note whose text contains HTML must be escaped (injected as HTML on the client)
    frag = build_flight_list(destination="<img src=x onerror=alert(1)>")[0]
    assert "<img" not in frag and "&lt;img" in frag


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
        "agentic_ui_demo.llm.AsyncOpenAI",
        _fake_openai(("render_flight_list", {"origin": "Graz", "destination": "Hamburg"})),
    )
    try:
        resp = client.post("/api/rsc/stream", json={"prompt": "flights Graz to Hamburg"})
        assert resp.status_code == 200
        events = _events(resp.text)
    finally:
        get_settings.cache_clear()

    assert events[0]["type"] == "tool" and events[0]["name"] == "render_flight_list"
    html_events = [e for e in events if e["type"] == "html"]
    assert any("<flight-card" in e["html"] for e in html_events)
    assert any('fid="AB123"' in e["html"] for e in html_events)
    assert events[-1]["type"] == "done"


def test_stream_composes_multiple_tools(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "agentic_ui_demo.llm.AsyncOpenAI",
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
    html_events = [e for e in events if e["type"] == "html"]
    assert any("Summary" in e["html"] for e in html_events)  # from render_summary
    assert any("<flight-card" in e["html"] for e in html_events)  # from render_flight_list


def test_stream_requires_key(client: TestClient, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()
    try:
        resp = client.post("/api/rsc/stream", json={"prompt": "hi"})
        assert resp.status_code == 503
    finally:
        get_settings.cache_clear()
