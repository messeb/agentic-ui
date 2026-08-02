"""Approach 5 — Server-streamed generative UI (RSC / v0 style).

The real thing uses Next.js + React Server Components + the Vercel AI SDK's ``streamUI``. This
stack is FastAPI + Nuxt, so this is the **framework-native equivalent** of the same pattern:

- The model **composes** a page by calling one or more server-side render tools (list, detail,
  delays overview, summary, note) — each "returns a component" / section.
- The server RENDERS each component to a **real HTML fragment** and **streams the fragments** over
  SSE; the client just mounts them (insertAdjacentHTML) — "streams it like text."
- The component set is **web components**: flight cards are emitted as the ``<flight-card>``
  custom element (registered once on the client) — standard, framework-agnostic ("write once,
  render everywhere"), unlike #3's Vue-only components. No code-gen, no sandbox.

Model-derived text is escaped before embedding (the fragments are injected as HTML).
Note: Vercel has paused AI SDK RSC development; this is here to illustrate the pattern.
"""

from __future__ import annotations

import asyncio
import html
import json
from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from openai import APIError
from pydantic import BaseModel, Field

from ..config import get_settings
from ..llm import chat_client
from .generative import DATASET

router = APIRouter(prefix="/rsc", tags=["rsc"])

STREAM_DELAY = 0.09  # simulate progressive server-side rendering


# --- server-side "components" — each renders to a REAL HTML fragment -----------
# The server produces actual markup; the client just mounts it. Flight cards are emitted as the
# <flight-card> **web component** (a standard custom element registered once on the client) —
# framework-agnostic, "write once, render everywhere", unlike #3's Vue-only components.
# Model-derived text is escaped (this HTML is injected via insertAdjacentHTML).


def _esc(value: object) -> str:
    return html.escape(str(value))


def _attr(value: object) -> str:
    return html.escape(str(value), quote=True)


def _heading(text: str) -> str:
    return f'<h2 class="text-base font-semibold text-slate-800">{_esc(text)}</h2>'


def _paragraph(text: str, muted: bool = False) -> str:
    cls = "text-slate-400" if muted else "text-slate-600"
    return f'<p class="text-sm {cls}">{_esc(text)}</p>'


def _flight_card(flight: dict[str, Any]) -> str:
    route = f"{flight['origin']} → {flight['destination']}"
    return (
        f'<flight-card fid="{_attr(flight["id"])}" route="{_attr(route)}" '
        f'date="{_attr(flight["date"])}" price="{_attr(flight["price"])}" '
        f'delay="{_attr(flight["delay_minutes"])}"></flight-card>'
    )


def _stat_row(pairs: list[tuple[str, str]]) -> str:
    cells = "".join(
        f'<div><div class="text-xs text-slate-400">{_esc(label)}</div>'
        f'<div class="font-medium text-slate-800">{_esc(value)}</div></div>'
        for label, value in pairs
    )
    return (
        '<div class="flex flex-wrap gap-6 rounded-lg border border-slate-200 bg-white p-3">'
        f"{cells}</div>"
    )


def _table(columns: list[str], rows: list[list[str]]) -> str:
    head = "".join(
        f'<th class="px-3 py-2 font-semibold text-slate-700">{_esc(c)}</th>' for c in columns
    )
    body = "".join(
        '<tr class="border-t border-slate-100">'
        + "".join(f'<td class="px-3 py-2 text-slate-700">{_esc(c)}</td>' for c in row)
        + "</tr>"
        for row in rows
    )
    return (
        '<div class="overflow-x-auto rounded-lg border border-slate-200">'
        f'<table class="w-full text-sm"><thead class="bg-slate-50 text-left"><tr>{head}</tr>'
        f"</thead><tbody>{body}</tbody></table></div>"
    )


def build_flight_list(
    origin: str | None = None,
    destination: str | None = None,
    only_delayed: bool = False,
    **_: Any,
) -> list[str]:
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
    fragments = [_heading(title)]
    matches = [
        f
        for f in DATASET
        if (not origin or f["origin"].lower() == origin.lower())
        and (not destination or f["destination"].lower() == destination.lower())
        and (not only_delayed or f["delay_minutes"] > 0)
    ]
    if not matches:
        fragments.append(_paragraph("No matching flights.", muted=True))
    fragments += [_flight_card(f) for f in matches]
    return fragments


def build_summary(**_: Any) -> list[str]:
    n = len(DATASET)
    avg = round(sum(f["price"] for f in DATASET) / n)
    on_time = round(100 * sum(1 for f in DATASET if f["delay_minutes"] == 0) / n)
    return [
        _heading("Summary"),
        _stat_row([("Flights", str(n)), ("Avg price", f"€{avg}"), ("On-time", f"{on_time}%")]),
    ]


def build_note(text: str = "", **_: Any) -> list[str]:
    return [_paragraph(text)]


def build_flight_detail(flight_id: str | None = None, **_: Any) -> list[str]:
    flight = next((x for x in DATASET if x["id"] == (flight_id or "").upper()), None)
    if flight is None:
        return [
            _heading("Flight not found"),
            _paragraph(f"No flight {flight_id!r} in the dataset.", muted=True),
        ]
    delay = flight["delay_minutes"]
    return [
        _heading(f"Flight {flight['id']}"),
        _flight_card(flight),
        _stat_row(
            [
                ("Price", f"€{flight['price']}"),
                ("Date", flight["date"]),
                ("Status", "On time" if delay == 0 else f"Delayed {delay}m"),
            ]
        ),
    ]


def build_delays_overview(**_: Any) -> list[str]:
    by_dest: dict[str, list[int]] = {}
    for f in DATASET:
        by_dest.setdefault(f["destination"], []).append(f["delay_minutes"])
    rows = [
        [dest, str(round(sum(delays) / len(delays))), str(len(delays))]
        for dest, delays in sorted(by_dest.items())
    ]
    return [
        _heading("Delays by destination"),
        _table(["Destination", "Avg delay (min)", "Flights"], rows),
    ]


BUILDERS = {
    "render_flight_list": build_flight_list,
    "render_flight_detail": build_flight_detail,
    "render_delays_overview": build_delays_overview,
    "render_summary": build_summary,
    "render_note": build_note,
}


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
    client = chat_client()
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
        yield _sse({"type": "html", "html": _paragraph(msg.content or "Nothing to render.")})
        yield _sse({"type": "done"})
        yield "data: [DONE]\n\n"
        return

    # The model composes the page from one or more render tools; stream each section's real HTML.
    for call in calls:
        name = call.function.name
        try:
            args = json.loads(call.function.arguments or "{}")
        except json.JSONDecodeError:
            args = {}
        yield _sse({"type": "tool", "name": name, "args": args})
        builder = BUILDERS.get(name)
        fragments = builder(**args) if builder else [_paragraph(f"Unknown view: {name}")]
        for fragment in fragments:
            yield _sse({"type": "html", "html": fragment})
            await asyncio.sleep(STREAM_DELAY)
    yield _sse({"type": "done"})
    yield "data: [DONE]\n\n"


@router.post("/stream", summary="Server-stream real HTML fragments (SSE)")
async def rsc_stream(req: RscRequest) -> StreamingResponse:
    if not get_settings().openai_api_key:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "OPENAI_API_KEY is not set on the server. Set it and restart the backend.",
        )
    return StreamingResponse(
        _stream(req.prompt),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
