"""Builds the LLM client in one place — chat-API-agnostic.

The backend speaks the OpenAI chat-completions API to whatever ``OPENAI_BASE_URL`` points at
(OpenAI, Azure OpenAI's OpenAI-compatible endpoint, a local Ollama / vLLM server, …). Every router
creates its client via :func:`chat_client`; tests patch ``AsyncOpenAI`` here.
"""

from __future__ import annotations

from openai import AsyncOpenAI

from .config import get_settings


def chat_client() -> AsyncOpenAI:
    """Return an async chat-completions client for the configured endpoint."""
    settings = get_settings()
    return AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url or None)
