"""Tests for approach #6 — context-driven adaptive UI inference layer."""

from __future__ import annotations

from fastapi import status
from fastapi.testclient import TestClient

from agentic_ui_demo.routers.adaptive import score_cards


def _primary(m: int, checked_in: bool = False, disruption: str = "none") -> str:
    return score_cards(m, checked_in, disruption)["primary"]


def test_far_out_shows_overview_first() -> None:
    # 28h before departure — before check-in opens (24h), so the overview leads.
    assert _primary(28 * 60) == "overview"


def test_checkin_window_promotes_checkin() -> None:
    # 20h out — inside the check-in window, not yet checked in.
    assert _primary(20 * 60) == "checkin"


def test_checked_in_demotes_checkin_to_leave_window() -> None:
    # 2h out and checked in → the "leave for the airport" card leads instead of check-in.
    assert _primary(120, checked_in=True) == "leave"


def test_boarding_window_promotes_boarding() -> None:
    assert _primary(30) == "boarding"


def test_disruption_always_wins() -> None:
    # A disruption jumps to the top regardless of the time window.
    for m in (28 * 60, 120, 30):
        assert _primary(m, disruption="delayed") == "disruption"
        assert _primary(m, disruption="gate_change") == "disruption"


def test_cancelled_hides_time_cards() -> None:
    plan = score_cards(30, checked_in=False, disruption="cancelled")
    assert plan["primary"] == "disruption"
    by_id = {c["id"]: c for c in plan["cards"]}
    assert by_id["boarding"]["visible"] is False
    assert by_id["checkin"]["visible"] is False


def test_delayed_detail_has_new_departure() -> None:
    plan = score_cards(120, disruption="delayed")
    detail = plan["disruption_detail"]
    assert detail["type"] == "delayed"
    assert detail["delay_min"] == 95
    # 08:35 + 95 min = 10:10.
    assert detail["new_departure"] == "10:10"


def test_cards_sorted_by_score_desc() -> None:
    cards = score_cards(20 * 60)["cards"]
    scores = [c["score"] for c in cards]
    assert scores == sorted(scores, reverse=True)


def test_get_trip(client: TestClient) -> None:
    resp = client.get("/api/adaptive")
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body["trip"]["flight_no"] == "OS 257"
    assert body["checkin_open"] == 1440


def test_infer_endpoint_needs_no_key(client: TestClient, monkeypatch) -> None:
    # Deterministic scorer — works with no OPENAI_API_KEY.
    from agentic_ui_demo.config import get_settings

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()
    try:
        resp = client.post(
            "/api/adaptive/infer",
            json={"minutes_to_departure": 30, "checked_in": False, "disruption": "none"},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["primary"] == "boarding"
    finally:
        get_settings.cache_clear()
