"""Approach 5 — Server-streamed generative UI (RSC / v0 style).

The real thing uses Next.js + React Server Components + the Vercel AI SDK's ``streamUI``. This
stack is FastAPI + Nuxt, so this is the **framework-native equivalent** of the same pattern:

- The model **composes** a page by calling one or more server-side render tools (list, detail,
  delays overview, summary, note) — each "returns a component" / section.
- The server builds a **serialized component tree** per section (whitelisted node types, not
  code) and **streams it node-by-node** over SSE, so the client renders progressively.
- The client maps each node to a real, pre-written Vue component. No code-gen, no sandbox.

Note: Vercel has paused AI SDK RSC development; this is here to illustrate the pattern.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from openai import APIError, AsyncOpenAI
from pydantic import BaseModel, Field

from ..config import get_settings
from .generative import DATASET

router = APIRouter(prefix="/rsc", tags=["rsc"])

STREAM_DELAY = 0.09  # simulate progressive server-side rendering


class Tree:
    """Accumulates a flat, ordered list of serialized nodes (parents before children)."""

    def __init__(self) -> None:
        self.nodes: list[dict[str, Any]] = []
        self._seq = 0

    def add(self, comp: str, props: dict[str, Any] | None = None, parent: str | None = None) -> str:
        self._seq += 1
        nid = f"n{self._seq}"
        self.nodes.append({"id": nid, "parent": parent, "comp": comp, "props": props or {}})
        return nid


def _card(flight: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": flight["id"],
        "origin": flight["origin"],
        "destination": flight["destination"],
        "date": flight["date"],
        "price": flight["price"],
        "delay": flight["delay_minutes"],
    }


def build_flight_list(
    origin: str | None = None,
    destination: str | None = None,
    only_delayed: bool = False,
    **_: Any,
) -> list[dict]:
    t = Tree()
    root = t.add("stack")
    if origin and destination:
        title = f"Flights {origin} → {destination}"
    elif destination:
        title = f"Flights to {destination}"
    elif origin:
        title = f"Flights from {origin}"
    else:
        title = "All flights"
    if only_delayed:
        title = f"Delayed — {title.lower()}"
    t.add("heading", {"text": title, "level": 2}, root)
    matches = [
        f
        for f in DATASET
        if (not origin or f["origin"].lower() == origin.lower())
        and (not destination or f["destination"].lower() == destination.lower())
        and (not only_delayed or f["delay_minutes"] > 0)
    ]
    if not matches:
        t.add("text", {"text": "No matching flights.", "muted": True}, root)
    for f in matches:
        t.add("flightCard", _card(f), root)
    return t.nodes


def build_summary(**_: Any) -> list[dict]:
    t = Tree()
    root = t.add("stack")
    t.add("heading", {"text": "Summary", "level": 2}, root)
    row = t.add("statRow", {}, root)
    n = len(DATASET)
    avg = round(sum(f["price"] for f in DATASET) / n)
    on_time = round(100 * sum(1 for f in DATASET if f["delay_minutes"] == 0) / n)
    t.add("stat", {"label": "Flights", "value": str(n)}, row)
    t.add("stat", {"label": "Avg price", "value": f"€{avg}"}, row)
    t.add("stat", {"label": "On-time", "value": f"{on_time}%"}, row)
    return t.nodes


def build_note(text: str = "", **_: Any) -> list[dict]:
    return [{"id": "n1", "parent": None, "comp": "text", "props": {"text": text}}]


def build_flight_detail(flight_id: str | None = None, **_: Any) -> list[dict]:
    t = Tree()
    root = t.add("stack")
    flight = next((x for x in DATASET if x["id"] == (flight_id or "").upper()), None)
    if flight is None:
        t.add("heading", {"text": "Flight not found", "level": 2}, root)
        t.add("text", {"text": f"No flight {flight_id!r} in the dataset.", "muted": True}, root)
        return t.nodes
    t.add("heading", {"text": f"Flight {flight['id']}", "level": 2}, root)
    t.add("flightCard", _card(flight), root)
    row = t.add("statRow", {}, root)
    t.add("stat", {"label": "Price", "value": f"€{flight['price']}"}, row)
    t.add("stat", {"label": "Date", "value": flight["date"]}, row)
    delay = flight["delay_minutes"]
    t.add(
        "stat", {"label": "Status", "value": "On time" if delay == 0 else f"Delayed {delay}m"}, row
    )
    return t.nodes


def build_delays_overview(**_: Any) -> list[dict]:
    t = Tree()
    root = t.add("stack")
    t.add("heading", {"text": "Delays by destination", "level": 2}, root)
    by_dest: dict[str, list[int]] = {}
    for f in DATASET:
        by_dest.setdefault(f["destination"], []).append(f["delay_minutes"])
    rows = [
        [dest, str(round(sum(delays) / len(delays))), str(len(delays))]
        for dest, delays in sorted(by_dest.items())
    ]
    t.add("table", {"columns": ["Destination", "Avg delay (min)", "Flights"], "rows": rows}, root)
    return t.nodes


BUILDERS = {
    "render_flight_list": build_flight_list,
    "render_flight_detail": build_flight_detail,
    "render_delays_overview": build_delays_overview,
    "render_summary": build_summary,
    "render_note": build_note,
}


def _reid(nodes: list[dict], prefix: str) -> list[dict]:
    """Namespace a builder's node ids so multiple sections don't collide in one stream."""
    return [
        {
            **n,
            "id": prefix + n["id"],
            "parent": (prefix + n["parent"]) if n["parent"] else None,
        }
        for n in nodes
    ]


TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "render_flight_list",
            "description": "Render a list of flights, optionally filtered by origin/destination "
            "and/or only delayed ones.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string"},
                    "destination": {"type": "string"},
                    "only_delayed": {"type": "boolean"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "render_flight_detail",
            "description": "Render details for one flight by its id (e.g. AB123).",
            "parameters": {
                "type": "object",
                "properties": {"flight_id": {"type": "string"}},
                "required": ["flight_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "render_delays_overview",
            "description": "Render an overview table of average delays per destination.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "render_summary",
            "description": "Render a compact stats panel (flights, average price, on-time %).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "render_note",
            "description": "Render a short line of explanatory text between sections.",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        },
    },
]

SYSTEM_PROMPT = (
    "You are a flight UI server that composes a page by calling render tools. Call ONE OR MORE "
    "tools, in a sensible order, to build the most helpful page for the request — each call adds "
    "a section that is streamed to the client.\n"
    "Tools: render_flight_list (searches/browsing; supports only_delayed), render_flight_detail "
    "(a specific flight id), render_delays_overview (delay table), render_summary (compact stats "
    "panel), render_note (a short explanatory line).\n"
    "Compose thoughtfully: e.g. a render_note intro + a filtered render_flight_list; or "
    "render_summary + render_delays_overview for an overview. Vary the composition to fit the ask."
)


class RscRequest(BaseModel):
    prompt: str = Field(min_length=1)


def _sse(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload)}\n\n"


async def _stream(prompt: str):
    client = AsyncOpenAI(api_key=get_settings().openai_api_key)
    try:
        resp = await client.chat.completions.create(
            model=get_settings().openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            tools=TOOLS,
            tool_choice="required",
        )
    except APIError as exc:
        yield _sse({"type": "error", "message": f"OpenAI error: {exc.message}"})
        yield "data: [DONE]\n\n"
        return

    msg = resp.choices[0].message
    calls = msg.tool_calls or []
    if not calls:
        for node in _reid([_text_node(msg.content or "Nothing to render.")], "t0_"):
            yield _sse({"type": "node", **node})
        yield _sse({"type": "done"})
        yield "data: [DONE]\n\n"
        return

    # The model composes the page from one or more render tools; stream each section in order.
    for idx, call in enumerate(calls):
        name = call.function.name
        try:
            args = json.loads(call.function.arguments or "{}")
        except json.JSONDecodeError:
            args = {}
        yield _sse({"type": "tool", "name": name, "args": args})
        builder = BUILDERS.get(name)
        nodes = builder(**args) if builder else [_text_node(f"Unknown view: {name}")]
        for node in _reid(nodes, f"t{idx}_"):
            yield _sse({"type": "node", **node})
            await asyncio.sleep(STREAM_DELAY)
    yield _sse({"type": "done"})
    yield "data: [DONE]\n\n"


def _text_node(text: str) -> dict[str, Any]:
    return {"id": "n1", "parent": None, "comp": "text", "props": {"text": text}}


@router.post("/stream", summary="Server-stream a serialized component tree (SSE)")
async def rsc_stream(req: RscRequest) -> StreamingResponse:
    if not get_settings().openai_api_key:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "OPENAI_API_KEY is not set on the server. Export it and restart the backend.",
        )
    return StreamingResponse(
        _stream(req.prompt),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
