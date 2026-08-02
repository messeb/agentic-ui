"""Approach 6 — Intent-based adaptive UI (context inference layer).

No chat surface. A single upcoming trip has a fixed departure. The client sends the trip's live
**context** — minutes until departure (a scrubber), whether the traveller has checked in, and any
operational **disruption** — and this **inference layer** scores each candidate card by contextual
relevance, returning an ordered layout + a rationale. The frontend renders the cards in that order,
emphasises the top one, and hides irrelevant ones (layout morphing).

Deterministic (no API key). In production the scorer would be an ML model over richer signals
(location, history, security-queue times) with the PII/consent obligations that implies. The
`rationale` counters the "why did it change?" opacity of such systems.
"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/adaptive", tags=["adaptive"])

TRIP: dict[str, Any] = {
    "id": "OS257",
    "flight_no": "OS 257",
    "airline": "AustroWings",
    "origin": "VIE",
    "origin_city": "Vienna",
    "destination": "LHR",
    "dest_city": "London",
    "date": "2026-08-14",
    "scheduled_departure": "08:35",
    "terminal": "3",
    "gate": "B24",
    "seat": "14C",
    "boarding_group": "2",
    "duration_min": 155,
}

# Disruption scenarios the user can trigger.
DELAY_MIN = 95
NEW_GATE = "C12"

Disruption = Literal["none", "delayed", "gate_change", "cancelled"]

# Windows (minutes before departure). Check-in opens 24h out, closes 1h out.
CHECKIN_OPEN, CHECKIN_CLOSE = 1440, 60
VISIBLE_THRESHOLD = 15


class InferRequest(BaseModel):
    minutes_to_departure: int
    checked_in: bool = False
    disruption: Disruption = "none"


def _add_minutes(hhmm: str, minutes: int) -> str:
    h, m = (int(x) for x in hhmm.split(":"))
    total = (h * 60 + m + minutes) % (24 * 60)
    return f"{total // 60:02d}:{total % 60:02d}"


def _disruption_detail(disruption: Disruption) -> dict[str, Any]:
    if disruption == "delayed":
        return {
            "type": "delayed",
            "delay_min": DELAY_MIN,
            "new_departure": _add_minutes(TRIP["scheduled_departure"], DELAY_MIN),
        }
    if disruption == "gate_change":
        return {"type": "gate_change", "new_gate": NEW_GATE, "old_gate": TRIP["gate"]}
    if disruption == "cancelled":
        return {"type": "cancelled"}
    return {"type": "none"}


def score_cards(
    m: int, checked_in: bool = False, disruption: Disruption = "none"
) -> dict[str, Any]:
    """Score each card 0..100 by contextual relevance; highest visible card is primary."""
    cancelled = disruption == "cancelled"
    gate = NEW_GATE if disruption == "gate_change" else TRIP["gate"]

    # Overview — always-present baseline.
    if m < 0:
        overview = (42, "You're in the air — flight has departed.")
    else:
        overview = (40, "Your upcoming trip at a glance.")

    # Check-in.
    if cancelled:
        checkin = (0, "")
    elif checked_in:
        checkin = (22, "Checked in ✓ — your boarding pass is ready.")
    elif CHECKIN_CLOSE <= m <= CHECKIN_OPEN:
        checkin = (80, "Check-in is open — it closes 1h before departure.")
    elif m > CHECKIN_OPEN:
        hrs = (m - CHECKIN_OPEN) // 60 + 1
        checkin = (26, f"Check-in opens in about {hrs}h (24h before departure).")
    else:
        checkin = (0, "")  # window closed

    # Leave for the airport.
    if cancelled or m < 0:
        leave = (0, "")
    elif 90 <= m <= 180:
        leave = (72, "Time to head to the airport — allow for security.")
    elif 180 < m <= 300:
        leave = (46, "Start wrapping up — you'll need to leave soon.")
    else:
        leave = (0, "")

    # Boarding.
    if cancelled or m < 0:
        boarding = (0, "")
    elif 0 <= m <= 45:
        boarding = (90, f"Boarding now at gate {gate} — group {TRIP['boarding_group']}.")
    elif 45 < m <= 90:
        boarding = (58, f"Boarding soon — head towards gate {gate}.")
    else:
        boarding = (0, "")

    # Disruption always jumps to the top while active.
    reasons = {
        "delayed": f"Flight delayed by {DELAY_MIN} min — new departure time below.",
        "gate_change": f"Gate changed to {NEW_GATE} — check the updated gate below.",
        "cancelled": "Flight cancelled — see rebooking options below.",
    }
    disruption_card = (100, reasons[disruption]) if disruption != "none" else (0, "")

    raw = {
        "overview": overview,
        "checkin": checkin,
        "leave": leave,
        "boarding": boarding,
        "disruption": disruption_card,
    }
    cards = [
        {"id": cid, "score": s, "visible": s >= VISIBLE_THRESHOLD, "reason": reason}
        for cid, (s, reason) in raw.items()
    ]
    cards.sort(key=lambda c: c["score"], reverse=True)
    primary = cards[0]["id"] if cards and cards[0]["visible"] else "overview"
    rationale = next(c["reason"] for c in cards if c["id"] == primary) or overview[1]

    return {
        "minutes_to_departure": m,
        "checked_in": checked_in,
        "disruption": disruption,
        "disruption_detail": _disruption_detail(disruption),
        "primary": primary,
        "rationale": rationale,
        "cards": cards,
    }


@router.get("", summary="The upcoming trip for the adaptive UI")
def get_data() -> dict[str, Any]:
    return {"trip": TRIP, "checkin_open": CHECKIN_OPEN, "checkin_close": CHECKIN_CLOSE}


@router.post("/infer", summary="Score the trip context into an ordered layout (inference layer)")
def infer(req: InferRequest) -> dict[str, Any]:
    return score_cards(req.minutes_to_departure, req.checked_in, req.disruption)
