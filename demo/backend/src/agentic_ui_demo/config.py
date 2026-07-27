"""Application settings, loaded from environment / .env."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# The manifest is vendored inside the package so the backend is standalone.
# (Sync it from demo/shared/approaches.json with `make sync-manifest`.)
_DEFAULT_MANIFEST = Path(__file__).resolve().parent / "data" / "approaches.json"


class Settings(BaseSettings):
    """Runtime configuration.

    All values can be overridden via environment variables (see `.env.example`).
    """

    model_config = SettingsConfigDict(env_prefix="DEMO_", env_file=".env", extra="ignore")

    app_name: str = "Agentic UI Demo API"
    environment: str = "development"

    # Path to the approaches manifest (vendored in the package by default).
    approaches_manifest: Path = _DEFAULT_MANIFEST

    # CORS origins allowed to call the API (the Nuxt frontend in dev).
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # --- Approach 1: Conversational chatbot (OpenAI) ---
    # Read from the GLOBAL `OPENAI_API_KEY` env var (no DEMO_ prefix), so the key
    # is never exposed to the frontend — the backend proxies all model calls.
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_model: str = "gpt-4o-mini"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
