"""A small in-memory flight domain and the tools the model may call.

Read-only tools run immediately; side-effect tools (``side_effect=True``) are gated
behind a human-in-the-loop permission step by the agent loop. This is a demo dataset —
state lives in module globals and can be reset with ``reset_state()``.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

# --- seed data ---------------------------------------------------------------

_SEED_FLIGHTS: list[dict[str, Any]] = [
    {
        "id": "AB123",
        "origin": "Graz",
        "destination": "Hamburg",
        "date": "2026-08-01",
        "price": 149,
        "seats": 4,
    },
    {
        "id": "AB124",
        "origin": "Graz",
        "destination": "Hamburg",
        "date": "2026-08-02",
        "price": 119,
        "seats": 2,
    },
    {
        "id": "CD200",
        "origin": "Vienna",
        "destination": "Berlin",
        "date": "2026-08-01",
        "price": 99,
        "seats": 9,
    },
    {
        "id": "CD201",
        "origin": "Vienna",
        "destination": "Berlin",
        "date": "2026-08-03",
        "price": 135,
        "seats": 0,
    },
    {
        "id": "EF300",
        "origin": "Graz",
        "destination": "London",
        "date": "2026-08-05",
        "price": 210,
        "seats": 5,
    },
]

_flights: list[dict[str, Any]] = []
_bookings: dict[str, dict[str, Any]] = {}
_booking_seq = 0


def reset_state() -> None:
    """Restore the demo dataset (used at startup and in tests)."""
    global _flights, _bookings, _booking_seq
    _flights = [dict(f) for f in _SEED_FLIGHTS]
    _bookings = {}
    _booking_seq = 0


reset_state()


def _find(flight_id: str) -> dict[str, Any] | None:
    return next((f for f in _flights if f["id"] == flight_id), None)


# --- tool handlers -----------------------------------------------------------


def search_flights(origin: str, destination: str, date: str | None = None) -> dict[str, Any]:
    matches = [
        f
        for f in _flights
        if f["origin"].lower() == origin.lower()
        and f["destination"].lower() == destination.lower()
        and (date is None or f["date"] == date)
    ]
    return {"count": len(matches), "flights": matches}


def get_flight(flight_id: str) -> dict[str, Any]:
    flight = _find(flight_id)
    if flight is None:
        return {"error": f"No flight with id {flight_id!r}."}
    return flight


def book_flight(flight_id: str, passenger: str) -> dict[str, Any]:
    global _booking_seq
    flight = _find(flight_id)
    if flight is None:
        return {"error": f"No flight with id {flight_id!r}."}
    if flight["seats"] <= 0:
        return {"error": f"Flight {flight_id} is sold out."}
    flight["seats"] -= 1
    _booking_seq += 1
    booking_id = f"BK{_booking_seq:03d}"
    _bookings[booking_id] = {
        "booking_id": booking_id,
        "flight_id": flight_id,
        "passenger": passenger,
    }
    return {"booked": True, **_bookings[booking_id], "seats_left": flight["seats"]}


def list_bookings() -> dict[str, Any]:
    return {"count": len(_bookings), "bookings": list(_bookings.values())}


def cancel_booking(booking_id: str) -> dict[str, Any]:
    booking = _bookings.pop(booking_id, None)
    if booking is None:
        return {"error": f"No booking with id {booking_id!r}."}
    flight = _find(booking["flight_id"])
    if flight is not None:
        flight["seats"] += 1
    return {"cancelled": True, "booking_id": booking_id}


# --- registry ----------------------------------------------------------------


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., dict[str, Any]]
    side_effect: bool = False
    required: list[str] = field(default_factory=list)


def _schema(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


REGISTRY: dict[str, Tool] = {
    t.name: t
    for t in [
        Tool(
            name="search_flights",
            description="Search flights by origin and destination (optionally an ISO date).",
            parameters=_schema(
                {
                    "origin": {"type": "string", "description": "Departure city, e.g. 'Graz'."},
                    "destination": {
                        "type": "string",
                        "description": "Arrival city, e.g. 'Hamburg'.",
                    },
                    "date": {
                        "type": "string",
                        "description": "Optional ISO date, e.g. '2026-08-01'.",
                    },
                },
                ["origin", "destination"],
            ),
            handler=search_flights,
        ),
        Tool(
            name="get_flight",
            description="Get full details for a single flight by its id.",
            parameters=_schema(
                {"flight_id": {"type": "string", "description": "Flight id, e.g. 'AB123'."}},
                ["flight_id"],
            ),
            handler=get_flight,
        ),
        Tool(
            name="list_bookings",
            description="List all current bookings.",
            parameters=_schema({}, []),
            handler=list_bookings,
        ),
        Tool(
            name="book_flight",
            description="Book a seat on a flight for a passenger. This charges the customer.",
            parameters=_schema(
                {
                    "flight_id": {
                        "type": "string",
                        "description": "Flight id to book, e.g. 'AB123'.",
                    },
                    "passenger": {"type": "string", "description": "Passenger full name."},
                },
                ["flight_id", "passenger"],
            ),
            handler=book_flight,
            side_effect=True,
        ),
        Tool(
            name="cancel_booking",
            description="Cancel an existing booking by its booking id.",
            parameters=_schema(
                {"booking_id": {"type": "string", "description": "Booking id, e.g. 'BK001'."}},
                ["booking_id"],
            ),
            handler=cancel_booking,
            side_effect=True,
        ),
    ]
}


def openai_tool_schemas() -> list[dict[str, Any]]:
    """Return the tool definitions in OpenAI function-calling format."""
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            },
        }
        for tool in REGISTRY.values()
    ]
