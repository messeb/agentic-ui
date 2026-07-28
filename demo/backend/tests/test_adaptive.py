"""Intent-based adaptive UI tests (approach #6).

Exercises the deterministic scoring layer — no API key involved.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from agentic_ui_demo.routers.adaptive import TEvent, score


def _views(*ids: str, dwell: int = 1000) -> list[TEvent]:
    return [TEvent(kind="view", flight_id=i, dwell_ms=dwell) for i in ids]


def test_no_signal_defaults_to_explore() -> None:
    plan = score([])
    assert plan["primary"] == "explore"
    assert plan["sort"] == "relevance"


def test_viewing_cheap_flights_and_sort_is_price() -> None:
    # AB124 (89), IJ501 (79), CD200 (99) are all below the median price.
    events = [*_views("AB124", "IJ501", "CD200"), TEvent(kind="sort", sort="price")]
    plan = score(events)
    assert plan["primary"] == "price"
    assert plan["sort"] == "price"
    assert "deals" in plan["emphasize"]
    assert plan["cta"] == "price_alert"


def test_sorting_by_duration_is_time() -> None:
    events = [*_views("CD201", "CD200"), TEvent(kind="sort", sort="duration")]
    plan = score(events)
    assert plan["primary"] == "time"
    assert plan["sort"] == "duration"
    assert "fastest" in plan["emphasize"]


def test_repeated_flight_is_urgency() -> None:
    events = [
        TEvent(kind="view", flight_id="GH401", dwell_ms=1500),
        TEvent(kind="view", flight_id="GH401", dwell_ms=2000),
        TEvent(kind="click", flight_id="GH401"),
    ]
    plan = score(events)
    assert plan["primary"] == "urgency"
    assert plan["focus_flight_id"] == "GH401"
    assert plan["emphasize"] == ["book"]
    assert plan["cta"] == "book"


def test_intents_are_bounded() -> None:
    plan = score([*_views("AB124"), TEvent(kind="sort", sort="price")])
    for value in plan["intents"].values():
        assert 0.0 <= value <= 1.0


def test_data_endpoint(client: TestClient) -> None:
    resp = client.get("/api/adaptive")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["flights"]) == 10
    assert {w["id"] for w in body["widgets"]} >= {"deals", "fastest", "book"}


def test_infer_endpoint(client: TestClient) -> None:
    resp = client.post(
        "/api/adaptive/infer",
        json={
            "events": [{"kind": "sort", "sort": "price"}, {"kind": "view", "flight_id": "AB124"}]
        },
    )
    assert resp.status_code == 200
    assert resp.json()["primary"] == "price"
