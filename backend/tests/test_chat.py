"""Streaming chat tests (approach #1) with a faked OpenAI client.

Verifies the SSE plumbing end-to-end without needing a real OPENAI_API_KEY.
"""

from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient

import agentic_ui_demo.routers.chat as chat_module
from agentic_ui_demo.config import get_settings


def _chunk(text: str) -> SimpleNamespace:
    """Mimic an OpenAI streaming chunk: chunk.choices[0].delta.content."""
    return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=text))])


class _FakeCompletions:
    async def create(self, **_kwargs):
        async def gen():
            for token in ["Hello", ", ", "**world**"]:
                yield _chunk(token)

        return gen()


class _FakeClient:
    def __init__(self, **_kwargs) -> None:
        self.chat = SimpleNamespace(completions=_FakeCompletions())


def test_chat_streams_sse_frames(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    get_settings.cache_clear()
    monkeypatch.setattr(chat_module, "AsyncOpenAI", _FakeClient)

    try:
        resp = client.post("/api/chat", json={"messages": [{"role": "user", "content": "hi"}]})
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        body = resp.text
        assert 'data: {"delta": "Hello"}' in body
        assert 'data: {"delta": "**world**"}' in body
        assert body.strip().endswith("data: [DONE]")
    finally:
        get_settings.cache_clear()
