"""Approach 6 — Intent-based adaptive UI (inference layer).

No chat surface. The client streams **implicit telemetry** (card hovers with dwell time, clicks,
sort taps); this **inference/scoring layer** turns those signals into intent probabilities and a
**layout plan** (how to re-rank flights, which widgets to emphasize/hide, which CTA to show).

The scorer here is a transparent heuristic (so it's testable and needs no API key). In production
this would be an ML model trained on behavioural data — with the PII/consent obligations that
implies. We also return a `rationale` to counter the "why did it move?" opacity of such systems.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/adaptive", tags=["adaptive"])

FLIGHTS: list[dict[str, Any]] = [
    {
        "id": "AB123",
        "origin": "Graz",
        "destination": "Hamburg",
        "date": "2026-08-01",
        "price": 149,
        "delay_minutes": 0,
        "duration_min": 95,
        "stops": 0,
        "airline": "AirGraz",
    },
    {
        "id": "AB124",
        "origin": "Graz",
        "destination": "Hamburg",
        "date": "2026-08-02",
        "price": 89,
        "delay_minutes": 35,
        "duration_min": 140,
        "stops": 1,
        "airline": "ValueWings",
    },
    {
        "id": "CD200",
        "origin": "Vienna",
        "destination": "Berlin",
        "date": "2026-08-01",
        "price": 99,
        "delay_minutes": 0,
        "duration_min": 80,
        "stops": 0,
        "airline": "AustroJet",
    },
    {
        "id": "CD201",
        "origin": "Vienna",
        "destination": "Berlin",
        "date": "2026-08-02",
        "price": 135,
        "delay_minutes": 0,
        "duration_min": 75,
        "stops": 0,
        "airline": "AustroJet",
    },
    {
        "id": "EF300",
        "origin": "Graz",
        "destination": "London",
        "date": "2026-08-01",
        "price": 210,
        "delay_minutes": 0,
        "duration_min": 150,
        "stops": 0,
        "airline": "AirGraz",
    },
    {
        "id": "EF301",
        "origin": "Graz",
        "destination": "London",
        "date": "2026-08-03",
        "price": 129,
        "delay_minutes": 20,
        "duration_min": 240,
        "stops": 1,
        "airline": "ValueWings",
    },
    {
        "id": "GH400",
        "origin": "Vienna",
        "destination": "Paris",
        "date": "2026-08-01",
        "price": 175,
        "delay_minutes": 0,
        "duration_min": 130,
        "stops": 0,
        "airline": "AustroJet",
    },
    {
        "id": "GH401",
        "origin": "Vienna",
        "destination": "Paris",
        "date": "2026-08-03",
        "price": 260,
        "delay_minutes": 0,
        "duration_min": 110,
        "stops": 0,
        "airline": "SkyPremium",
    },
    {
        "id": "IJ500",
        "origin": "Graz",
        "destination": "Rome",
        "date": "2026-08-02",
        "price": 199,
        "delay_minutes": 0,
        "duration_min": 165,
        "stops": 0,
        "airline": "AirGraz",
    },
    {
        "id": "IJ501",
        "origin": "Graz",
        "destination": "Rome",
        "date": "2026-08-04",
        "price": 79,
        "delay_minutes": 45,
        "duration_min": 300,
        "stops": 2,
        "airline": "ValueWings",
    },
]

WIDGETS: list[dict[str, str]] = [
    {"id": "deals", "title": "Deals", "description": "Cheapest flights right now"},
    {"id": "fastest", "title": "Fastest routes", "description": "Shortest total travel time"},
    {"id": "popular", "title": "Popular destinations", "description": "Where people fly most"},
    {"id": "price_alert", "title": "Price alert", "description": "Get notified when prices drop"},
    {"id": "book", "title": "Ready to book", "description": "Finish the flight you keep viewing"},
    {"id": "assistant", "title": "Need help?", "description": "Ask our travel assistant"},
]

Primary = Literal["price", "time", "urgency", "explore"]

EMPHASIZE: dict[str, list[str]] = {
    "price": ["deals", "price_alert"],
    "time": ["fastest"],
    "urgency": ["book"],
    "explore": ["popular", "deals"],
}
HIDE: dict[str, list[str]] = {
    "price": ["fastest", "book", "assistant"],
    "time": ["deals", "price_alert", "book", "assistant"],
    "urgency": ["popular", "deals", "assistant"],
    "explore": ["book", "price_alert"],
}
CTA: dict[str, str] = {
    "price": "price_alert",
    "time": "fastest",
    "urgency": "book",
    "explore": "popular",
}
SORT: dict[str, str] = {
    "price": "price",
    "time": "duration",
    "urgency": "relevance",
    "explore": "relevance",
}


class TEvent(BaseModel):
    kind: Literal["view", "click", "sort"]
    flight_id: str | None = None
    dwell_ms: int | None = None
    sort: Literal["price", "duration"] | None = None


class InferRequest(BaseModel):
    events: list[TEvent] = Field(default_factory=list)


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[len(ordered) // 2] if ordered else 0.0


def _rationale(primary: str, sort_by: str | None, focus: str | None) -> str:
    if primary == "price":
        extra = " and sorted by price" if sort_by == "price" else ""
        return f"You kept viewing cheaper flights{extra} — re-ranked by price and surfaced Deals."
    if primary == "time":
        extra = " and sorted by duration" if sort_by == "duration" else ""
        return f"You favoured the fastest options{extra} — re-ranked by duration, surfaced Fastest."
    if primary == "urgency":
        ref = f" {focus}" if focus else " one flight"
        return f"You keep returning to{ref} — moved Book to the top and hid distractions."
    return "You're browsing broadly — showing popular destinations and deals."


def score(events: list[TEvent]) -> dict[str, Any]:
    by_id = {f["id"]: f for f in FLIGHTS}
    views = [e for e in events if e.kind == "view"]
    clicks = [e for e in events if e.kind == "click"]
    sort_events = [e for e in events if e.kind == "sort"]
    sort_by = sort_events[-1].sort if sort_events else None

    engaged = [by_id[e.flight_id] for e in (views + clicks) if e.flight_id in by_id]
    n = len(engaged)

    # Score price/time preference over DISTINCT flights (so repeatedly viewing one flight
    # doesn't masquerade as a preference), damped by how many distinct flights were seen.
    distinct = list({f["id"]: f for f in engaged}.values())
    d = len(distinct)
    confidence = min(d, 3) / 3

    median_price = _median([f["price"] for f in FLIGHTS])
    median_dur = _median([f["duration_min"] for f in FLIGHTS])

    price_frac = (sum(1 for f in distinct if f["price"] <= median_price) / d) if d else 0.0
    time_frac = (sum(1 for f in distinct if f["duration_min"] <= median_dur) / d) if d else 0.0
    price_score = price_frac * confidence
    time_score = time_frac * confidence
    if sort_by == "price":  # an explicit sort tap is a strong, decisive signal
        price_score = min(1.0, price_score + 0.5)
    if sort_by == "duration":
        time_score = min(1.0, time_score + 0.5)

    counts = Counter(e.flight_id for e in (views + clicks) if e.flight_id)
    top_id, top_count = counts.most_common(1)[0] if counts else (None, 0)
    focus = top_id if top_count >= 2 else None
    urgency_score = min(1.0, max(0, top_count - 1) * 0.3 + len(clicks) * 0.25)

    dests = Counter(f["destination"] for f in engaged)
    concentration = (max(dests.values()) / n) if n else 0.0
    explore_score = round(1.0 - concentration, 2) if n else 0.5

    ranked = {"price": price_score, "time": time_score, "urgency": urgency_score}
    # Tie-break toward the intent matching the latest sort tap; otherwise urgency wins ties.
    if sort_by == "duration":
        order = ["time", "urgency", "price"]
    elif sort_by == "price":
        order = ["price", "urgency", "time"]
    else:
        order = ["urgency", "price", "time"]
    primary = max(order, key=lambda k: (ranked[k], -order.index(k)))
    if ranked[primary] < 0.34:
        primary = "explore"

    return {
        "intents": {
            "price": round(price_score, 2),
            "time": round(time_score, 2),
            "urgency": round(urgency_score, 2),
            "explore": round(explore_score, 2),
        },
        "primary": primary,
        "sort": SORT[primary],
        "emphasize": EMPHASIZE[primary],
        "hide": HIDE[primary],
        "cta": CTA[primary],
        "focus_flight_id": focus,
        "rationale": _rationale(primary, sort_by, focus),
    }


@router.get("", summary="Flights + widget catalog for the adaptive UI")
def get_data() -> dict[str, Any]:
    return {"flights": FLIGHTS, "widgets": WIDGETS}


@router.post("/infer", summary="Score telemetry into a layout plan (inference layer)")
def infer(req: InferRequest) -> dict[str, Any]:
    return score(req.events)
