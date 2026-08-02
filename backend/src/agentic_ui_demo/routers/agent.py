"""Approach 7 — Agentic frontend ("UI as toolbox").

Every UI mutation is exposed as a flat tool (update_form, set_filter, sort_flights, goto,
select_flight, book, finish). The client holds the reactive store and a generic dispatcher; this
backend is **stateless** — each turn it rebuilds the system prompt from the posted live state
("the prompt *is* the state") and returns the next tool calls. Deterministic flow (filtering,
rendering) stays in the frontend; only the interpretive "what to do next" goes to the model.

Every tool call carries a `next` directive (continue / await_user / done) that drives the loop.
`book` is destructive and gated by a human-in-the-loop confirmation on the client.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException, status
from openai import APIError, AsyncOpenAI
from pydantic import BaseModel, Field

from ..config import get_settings

router = APIRouter(prefix="/agent", tags=["agent"])

MAX_TOOL_CALLS = 6

FLIGHTS: list[dict[str, Any]] = [
    {
        "id": "AB123",
        "origin": "Graz",
        "destination": "Hamburg",
        "date": "2026-08-03",
        "price": 149,
        "duration_min": 95,
        "stops": 0,
        "departure_time": "07:30",
    },
    {
        "id": "AB124",
        "origin": "Graz",
        "destination": "Hamburg",
        "date": "2026-08-03",
        "price": 89,
        "duration_min": 140,
        "stops": 1,
        "departure_time": "14:10",
    },
    {
        "id": "AB125",
        "origin": "Graz",
        "destination": "Hamburg",
        "date": "2026-08-03",
        "price": 119,
        "duration_min": 100,
        "stops": 0,
        "departure_time": "09:05",
    },
    {
        "id": "CD200",
        "origin": "Vienna",
        "destination": "Berlin",
        "date": "2026-08-03",
        "price": 99,
        "duration_min": 80,
        "stops": 0,
        "departure_time": "06:45",
    },
    {
        "id": "CD201",
        "origin": "Vienna",
        "destination": "Berlin",
        "date": "2026-08-03",
        "price": 135,
        "duration_min": 75,
        "stops": 0,
        "departure_time": "18:20",
    },
    {
        "id": "EF300",
        "origin": "Graz",
        "destination": "London",
        "date": "2026-08-03",
        "price": 210,
        "duration_min": 150,
        "stops": 0,
        "departure_time": "08:15",
    },
    {
        "id": "EF301",
        "origin": "Graz",
        "destination": "London",
        "date": "2026-08-03",
        "price": 129,
        "duration_min": 240,
        "stops": 1,
        "departure_time": "16:40",
    },
    {
        "id": "GH400",
        "origin": "Vienna",
        "destination": "Paris",
        "date": "2026-08-03",
        "price": 175,
        "duration_min": 130,
        "stops": 0,
        "departure_time": "10:00",
    },
]

_NEXT = {
    "type": "string",
    "enum": ["continue", "await_user", "done"],
    "description": "Flow directive: 'continue' if you will act again, 'await_user' if you need "
    "the user, 'done' when the goal is met.",
}


def _tool(
    name: str, description: str, props: dict[str, Any], required: list[str]
) -> dict[str, Any]:
    props = {**props, "next": _NEXT}
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": props,
                "required": [*required, "next"],
            },
        },
    }


TOOLS: list[dict[str, Any]] = [
    _tool(
        "update_form",
        "Set a search form field.",
        {
            "field": {
                "type": "string",
                "enum": ["origin", "destination", "date", "passengers", "cabin"],
            },
            "value": {"type": "string"},
        },
        ["field", "value"],
    ),
    _tool(
        "set_filter",
        "Set a results filter. value: 'true'/'false' for morning_only/direct_only, "
        "or a number for max_price.",
        {
            "filter": {"type": "string", "enum": ["max_price", "morning_only", "direct_only"]},
            "value": {"type": "string"},
        },
        ["filter", "value"],
    ),
    _tool(
        "sort_flights",
        "Sort the visible flights.",
        {"by": {"type": "string", "enum": ["price", "duration"]}},
        ["by"],
    ),
    _tool(
        "goto",
        "Navigate to a step.",
        {"step": {"type": "string", "enum": ["search", "results", "review"]}},
        ["step"],
    ),
    _tool(
        "select_flight",
        "Select a flight by id (must be one of the visible flights).",
        {"flight_id": {"type": "string"}},
        ["flight_id"],
    ),
    _tool("book", "Book the selected flight. Destructive — requires user confirmation.", {}, []),
    _tool(
        "finish",
        "Signal the goal is complete with a short summary.",
        {"message": {"type": "string"}},
        ["message"],
    ),
]

SYSTEM_PREFIX = (
    "You operate a flight-booking app by calling UI tools — every UI change IS a tool. Take the "
    "next best action(s) toward the user's GOAL, then call finish.\n"
    "Flow: fill the form (update_form) → goto('results') → optionally set_filter/sort_flights → "
    "select_flight (only from VISIBLE flights) → book (to purchase; it asks the user to confirm). "
    "When the goal is met (or right after booking), call finish with a one-line summary.\n"
    "Rules: every call MUST include `next`. Do NOT repeat an action already reflected in STATE "
    "(e.g. don't set a field that already has that value). Only select from the visible flights."
)


class AgentStepRequest(BaseModel):
    goal: str = Field(min_length=1)
    state: dict[str, Any] = Field(default_factory=dict)


def _build_messages(goal: str, state: dict[str, Any]) -> list[dict[str, str]]:
    # Static prefix first (stable → benefits from OpenAI prompt caching); dynamic state after.
    return [
        {"role": "system", "content": SYSTEM_PREFIX},
        {"role": "user", "content": f"GOAL: {goal}\n\nSTATE:\n{json.dumps(state, indent=0)}"},
    ]


@router.get("/data", summary="Flights for the agentic workspace")
def get_data() -> dict[str, Any]:
    return {"flights": FLIGHTS}


@router.post("/step", summary="Get the next tool call(s) from live state (stateless)")
async def step(req: AgentStepRequest) -> dict[str, Any]:
    settings = get_settings()
    if not settings.openai_api_key:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "OPENAI_API_KEY is not set on the server. Export it and restart the backend.",
        )

    client = AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url or None)
    try:
        resp = await client.chat.completions.create(
            model=settings.openai_model,
            messages=_build_messages(req.goal, req.state),
            tools=TOOLS,
            tool_choice="required",
        )
    except APIError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"OpenAI error: {exc.message}") from exc

    msg = resp.choices[0].message
    calls = []
    for call in msg.tool_calls or []:
        try:
            args = json.loads(call.function.arguments or "{}")
        except json.JSONDecodeError:
            args = {}
        calls.append({"name": call.function.name, "args": args, "next": args.get("next", "done")})
    return {"calls": calls[:MAX_TOOL_CALLS], "text": msg.content or ""}
