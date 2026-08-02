"""Approach 8 — Protocol-decoupled agents (MCP · MCP-UI · AG-UI).

An architectural layer, not a UI rung. This endpoint emits an **AG-UI-style typed event stream**
so the frontend is a pure function of the protocol (swap the agent/backend, the UI is unchanged):

- lifecycle: RUN_STARTED / STEP_STARTED / STEP_FINISHED / RUN_FINISHED / RUN_ERROR
- text message: TEXT_MESSAGE_START / TEXT_MESSAGE_CONTENT (deltas) / TEXT_MESSAGE_END
- tool call: TOOL_CALL_START / TOOL_CALL_ARGS / TOOL_CALL_END / TOOL_CALL_RESULT
- state: STATE_SNAPSHOT (full) / STATE_DELTA (RFC-6902 JSON Patch) / MESSAGES_SNAPSHOT
- special: RAW / CUSTOM

A tool result can carry an **MCP-UI** resource (`ui://` HTML) that the client renders in a
sandboxed iframe and which posts intents back via `postMessage`. The model only resolves the NL
prompt into a small intent; the emphasis is the protocol, not the reasoning.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from openai import APIError, AsyncOpenAI
from pydantic import BaseModel, Field

from ..config import get_settings
from .agent import FLIGHTS

router = APIRouter(prefix="/protocol", tags=["protocol"])

# The 16 AG-UI event types across five groups (for the UI legend + tests).
EVENT_TYPES: dict[str, list[str]] = {
    "lifecycle": ["RUN_STARTED", "RUN_FINISHED", "RUN_ERROR", "STEP_STARTED", "STEP_FINISHED"],
    "text": ["TEXT_MESSAGE_START", "TEXT_MESSAGE_CONTENT", "TEXT_MESSAGE_END"],
    "tool_call": ["TOOL_CALL_START", "TOOL_CALL_ARGS", "TOOL_CALL_END", "TOOL_CALL_RESULT"],
    "state": ["STATE_SNAPSHOT", "STATE_DELTA"],
    "special": ["RAW", "CUSTOM"],
}

PROTOCOLS = [
    {
        "name": "MCP",
        "connects": "agent → tools",
        "role": "JSON-RPC access to tools/resources/prompts",
    },
    {
        "name": "MCP-UI",
        "connects": "agent → generative UI",
        "role": "tool returns a ui:// HTML resource in a sandboxed iframe",
    },
    {
        "name": "AG-UI",
        "connects": "agent → user interface",
        "role": "typed event stream syncing agent activity to the UI",
    },
]

INTENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["action", "origin", "destination", "flight_id", "message"],
    "properties": {
        "action": {"type": "string", "enum": ["search", "show", "book"]},
        "origin": {"type": ["string", "null"]},
        "destination": {"type": ["string", "null"]},
        "flight_id": {"type": ["string", "null"]},
        "message": {"type": "string"},
    },
}

SYSTEM_PROMPT = (
    "Resolve the user's flight request into an intent. action: 'search' (browse/filter flights), "
    "'show' (render a rich card for a specific flight id), or 'book' (book a specific flight id). "
    "Fill origin/destination for search, flight_id for show/book (null otherwise). `message` is a "
    "one-line natural summary of what you did."
)

STREAM_DELAY = 0.05


class RunRequest(BaseModel):
    prompt: str = Field(min_length=1)
    thread_id: str | None = None


def _ev(event_type: str, **data: Any) -> str:
    return f"data: {json.dumps({'type': event_type, **data})}\n\n"


def _match(origin: str | None, destination: str | None) -> list[dict[str, Any]]:
    return [
        f
        for f in FLIGHTS
        if (not origin or f["origin"].lower() == origin.lower())
        and (not destination or f["destination"].lower() == destination.lower())
    ]


def _ui_card(flight: dict[str, Any]) -> str:
    """A self-contained MCP-UI ui:// HTML resource with a postMessage-back button."""
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; "
        "script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'\">"
        "<style>body{margin:0;font:13px system-ui;color:#0b1020}.c{border:1px solid #e2e8f0;"
        "border-radius:10px;padding:12px}.r{display:flex;justify-content:space-between;align-items:center}"
        "b{font-size:15px}button{margin-top:8px;width:100%;border:0;border-radius:8px;background:#0b1020;"
        "color:#fff;padding:8px;font-weight:600;cursor:pointer}.m{color:#64748b;font-size:12px}</style>"
        "</head><body><div class='c'><div class='r'><b>"
        + flight["id"]
        + "</b><b>€"
        + str(flight["price"])
        + "</b></div>"
        "<div class='m'>"
        + flight["origin"]
        + " → "
        + flight["destination"]
        + " · "
        + flight["departure_time"]
        + " · "
        + str(flight["duration_min"])
        + " min</div>"
        "<button id='b'>Book " + flight["id"] + "</button></div>"
        "<script>document.getElementById('b').onclick=function(){parent.postMessage("
        "{type:'mcp-ui:intent',tool:'book_flight',args:{flight_id:'" + flight["id"] + "'}},'*')}"
        "</scr" + "ipt></body></html>"
    )


async def _run(intent: dict[str, Any], thread_id: str):
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    yield _ev("RUN_STARTED", threadId=thread_id, runId=run_id)
    yield _ev("STEP_STARTED", stepName="resolve")

    action = intent["action"]
    tool_name = {"search": "search_flights", "show": "show_flight", "book": "book_flight"}[action]
    args = {k: intent[k] for k in ("origin", "destination", "flight_id") if intent.get(k)}
    tcid = f"tc_{uuid.uuid4().hex[:8]}"
    yield _ev("TOOL_CALL_START", toolCallId=tcid, toolCallName=tool_name)
    yield _ev("TOOL_CALL_ARGS", toolCallId=tcid, delta=json.dumps(args))
    yield _ev("TOOL_CALL_END", toolCallId=tcid)
    await asyncio.sleep(STREAM_DELAY)

    if action == "search":
        flights = _match(intent.get("origin"), intent.get("destination"))
        yield _ev("TOOL_CALL_RESULT", toolCallId=tcid, content=json.dumps({"count": len(flights)}))
        yield _ev("STATE_SNAPSHOT", snapshot={"flights": flights, "booking": None})
    elif action == "show":
        flight = next(
            (f for f in FLIGHTS if f["id"] == (intent.get("flight_id") or "").upper()), None
        )
        if flight:
            resource = {
                "uri": f"ui://flight/{flight['id']}",
                "mimeType": "text/html",
                "text": _ui_card(flight),
            }
            yield _ev(
                "TOOL_CALL_RESULT",
                toolCallId=tcid,
                content={"type": "resource", "resource": resource},
            )
            yield _ev("STATE_SNAPSHOT", snapshot={"flights": [flight], "booking": None})
        else:
            yield _ev(
                "TOOL_CALL_RESULT", toolCallId=tcid, content=json.dumps({"error": "not found"})
            )
            yield _ev("STATE_SNAPSHOT", snapshot={"flights": [], "booking": None})
    else:  # book
        flight = next(
            (f for f in FLIGHTS if f["id"] == (intent.get("flight_id") or "").upper()), None
        )
        yield _ev(
            "STATE_SNAPSHOT", snapshot={"flights": [flight] if flight else [], "booking": None}
        )
        if flight:
            booking = {
                "flight_id": flight["id"],
                "status": "confirmed",
                "ref": f"BK{uuid.uuid4().hex[:6].upper()}",
            }
            # RFC-6902 JSON Patch: add the booking to state without resending the whole snapshot.
            yield _ev("STATE_DELTA", delta=[{"op": "add", "path": "/booking", "value": booking}])
            yield _ev("TOOL_CALL_RESULT", toolCallId=tcid, content=json.dumps(booking))
        else:
            yield _ev(
                "TOOL_CALL_RESULT", toolCallId=tcid, content=json.dumps({"error": "not found"})
            )

    await asyncio.sleep(STREAM_DELAY)
    mid = f"msg_{uuid.uuid4().hex[:8]}"
    yield _ev("TEXT_MESSAGE_START", messageId=mid, role="assistant")
    for word in (intent["message"] or "Done.").split(" "):
        yield _ev("TEXT_MESSAGE_CONTENT", messageId=mid, delta=word + " ")
        await asyncio.sleep(STREAM_DELAY)
    yield _ev("TEXT_MESSAGE_END", messageId=mid)

    yield _ev(
        "CUSTOM",
        name="demo.note",
        value="This whole view was driven by AG-UI events — swap the backend, the UI is unchanged.",
    )
    yield _ev("STEP_FINISHED", stepName="resolve")
    yield _ev("RUN_FINISHED", threadId=thread_id, runId=run_id)
    yield "data: [DONE]\n\n"


@router.get("/info", summary="Protocol legend (protocols + AG-UI event types)")
def info() -> dict[str, Any]:
    return {"protocols": PROTOCOLS, "event_types": EVENT_TYPES}


@router.post("/run", summary="Run an agent turn as an AG-UI event stream (SSE)")
async def run(req: RunRequest) -> StreamingResponse:
    settings = get_settings()
    if not settings.openai_api_key:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "OPENAI_API_KEY is not set on the server. Export it and restart the backend.",
        )
    client = AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url or None)
    thread_id = req.thread_id or f"thread_{uuid.uuid4().hex[:8]}"

    try:
        resp = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": req.prompt},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "intent", "strict": True, "schema": INTENT_SCHEMA},
            },
        )
        intent = json.loads(resp.choices[0].message.content or "{}")
    except APIError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"OpenAI error: {exc.message}") from exc

    return StreamingResponse(
        _run(intent, thread_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
