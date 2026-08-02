"""Approach 1 — Conversational chatbot.

A thin proxy in front of OpenAI: it holds the API key (never the frontend), forwards the
conversation, and streams the model's tokens back to the browser as Server-Sent Events (SSE).
The model only talks — it has no access to app state or actions.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Literal

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from openai import APIError, AsyncOpenAI
from pydantic import BaseModel, Field

from ..config import get_settings

router = APIRouter(prefix="/chat", tags=["chat"])

SYSTEM_PROMPT = (
    "You are a concise, friendly assistant embedded in a demo app. "
    "Answer in GitHub-flavored Markdown. Use fenced code blocks with a language tag "
    "for any code. Keep answers focused."
)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1)
    model: str | None = None


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


async def _stream(messages: list[dict], model: str) -> AsyncIterator[str]:
    client = AsyncOpenAI(
        api_key=get_settings().openai_api_key,
        base_url=get_settings().openai_base_url or None,
    )
    try:
        stream = await client.chat.completions.create(model=model, messages=messages, stream=True)
        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta.content
            if delta:
                yield _sse({"delta": delta})
    except APIError as exc:  # surface a clean error to the client instead of crashing the stream
        yield _sse({"error": f"OpenAI error: {exc.message}"})
    finally:
        yield "data: [DONE]\n\n"


@router.post("", summary="Stream a chat completion over SSE")
async def chat(req: ChatRequest) -> StreamingResponse:
    settings = get_settings()
    if not settings.openai_api_key:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "OPENAI_API_KEY is not set on the server. Export it and restart the backend.",
        )

    model = req.model or settings.openai_model
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += [m.model_dump() for m in req.messages]

    return StreamingResponse(
        _stream(messages, model),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
