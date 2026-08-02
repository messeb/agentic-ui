"""Approach 2 — Function / Tool Calling.

Runs the agent loop (reason -> act -> observe -> repeat): the model may emit tool calls
instead of prose; a dispatcher runs the matching handler, appends the result to the
conversation, and the model is re-invoked until it returns a final answer.

Read-only tools execute immediately. Side-effect tools are gated behind a human-in-the-loop
**permission** step: the loop pauses and streams an ``awaiting_permission`` event; the client
re-invokes with an approval decision to resume. The full message list is streamed back in a
``state`` event so the (stateless) client can resend it.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from openai import APIError, AsyncOpenAI
from pydantic import BaseModel, Field

from ..config import get_settings
from ..tools import REGISTRY, openai_tool_schemas

router = APIRouter(prefix="/tools", tags=["tools"])

MAX_STEPS = 6

SYSTEM_PROMPT = (
    "You are a flight booking assistant. Use the provided tools to search flights, look up "
    "details, and manage bookings. Prefer calling a tool over guessing. When you have enough "
    "information, answer concisely in GitHub-flavored Markdown. Booking or cancelling requires "
    "the user's confirmation — the app enforces this, so just request the action when appropriate."
)


class ToolChatRequest(BaseModel):
    messages: list[dict[str, Any]] = Field(min_length=1)
    # Decisions for side-effect tool calls, keyed by tool_call id: {id: approved?}.
    approvals: dict[str, bool] = Field(default_factory=dict)


def _sse(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload)}\n\n"


def _parse_args(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _assistant_dict(msg: Any) -> dict[str, Any]:
    """Convert an OpenAI response message with tool calls into a plain, serializable dict."""
    return {
        "role": "assistant",
        "content": msg.content or "",
        "tool_calls": [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in (msg.tool_calls or [])
        ],
    }


def _run_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    tool = REGISTRY.get(name)
    if tool is None:
        return {"error": f"Unknown tool {name!r}."}
    try:
        return tool.handler(**args)
    except TypeError as exc:
        return {"error": f"Invalid arguments for {name}: {exc}"}


def _needs_approval(call: dict[str, Any], approvals: dict[str, bool]) -> bool:
    name = call["function"]["name"]
    tool = REGISTRY.get(name)
    return bool(tool and tool.side_effect) and call["id"] not in approvals


def _resolve_calls(
    calls: list[dict[str, Any]], approvals: dict[str, bool]
) -> Iterator[tuple[dict[str, Any], dict[str, Any]]]:
    """Yield (tool_message, event) for each call — executing it or recording a denial."""
    for call in calls:
        cid = call["id"]
        name = call["function"]["name"]
        args = _parse_args(call["function"]["arguments"])
        tool = REGISTRY.get(name)

        if tool and tool.side_effect and approvals.get(cid) is False:
            result: dict[str, Any] = {"denied": True, "message": "User declined this action."}
            denied = True
        else:
            result = _run_tool(name, args)
            denied = False

        message = {"role": "tool", "tool_call_id": cid, "name": name, "content": json.dumps(result)}
        event = {"type": "tool_result", "id": cid, "name": name, "result": result, "denied": denied}
        yield message, event


def _client_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Everything except the server-side system prompt (messages[0])."""
    return messages[1:]


async def _run(messages_in: list[dict[str, Any]], approvals: dict[str, bool]) -> AsyncIterator[str]:
    client = AsyncOpenAI(
        api_key=get_settings().openai_api_key,
        base_url=get_settings().openai_base_url or None,
    )
    model = get_settings().openai_model
    messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += [m for m in messages_in if m.get("role") != "system"]

    try:
        # Resume: resolve any dangling tool calls left awaiting a decision.
        tail = messages[-1]
        if tail.get("role") == "assistant" and tail.get("tool_calls"):
            for message, event in _resolve_calls(tail["tool_calls"], approvals):
                messages.append(message)
                yield _sse(event)

        for _ in range(MAX_STEPS):
            resp = await client.chat.completions.create(
                model=model,
                messages=messages,
                tools=openai_tool_schemas(),
                tool_choice="auto",
            )
            msg = resp.choices[0].message

            if not msg.tool_calls:
                content = msg.content or ""
                messages.append({"role": "assistant", "content": content})
                yield _sse({"type": "final", "content": content})
                yield _sse({"type": "state", "messages": _client_messages(messages)})
                yield "data: [DONE]\n\n"
                return

            assistant = _assistant_dict(msg)
            messages.append(assistant)
            if msg.content:
                yield _sse({"type": "assistant_text", "content": msg.content})

            calls = assistant["tool_calls"]
            for call in calls:
                name = call["function"]["name"]
                tool = REGISTRY.get(name)
                yield _sse(
                    {
                        "type": "tool_call",
                        "id": call["id"],
                        "name": name,
                        "args": _parse_args(call["function"]["arguments"]),
                        "side_effect": bool(tool and tool.side_effect),
                    }
                )

            pending = [c for c in calls if _needs_approval(c, approvals)]
            if pending:
                yield _sse(
                    {
                        "type": "awaiting_permission",
                        "calls": [
                            {
                                "id": c["id"],
                                "name": c["function"]["name"],
                                "args": _parse_args(c["function"]["arguments"]),
                            }
                            for c in pending
                        ],
                    }
                )
                yield _sse({"type": "state", "messages": _client_messages(messages)})
                yield "data: [DONE]\n\n"
                return

            for message, event in _resolve_calls(calls, approvals):
                messages.append(message)
                yield _sse(event)

        yield _sse({"type": "error", "message": "Reached the step limit without a final answer."})
        yield "data: [DONE]\n\n"
    except APIError as exc:
        yield _sse({"type": "error", "message": f"OpenAI error: {exc.message}"})
        yield "data: [DONE]\n\n"


@router.get("", summary="List the available tools")
def list_tools() -> dict[str, Any]:
    return {
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "side_effect": t.side_effect,
                "parameters": t.parameters,
            }
            for t in REGISTRY.values()
        ]
    }


@router.post("/chat", summary="Run the tool-calling agent loop (SSE)")
async def tool_chat(req: ToolChatRequest) -> StreamingResponse:
    if not get_settings().openai_api_key:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "OPENAI_API_KEY is not set on the server. Export it and restart the backend.",
        )
    return StreamingResponse(
        _run(req.messages, req.approvals),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
