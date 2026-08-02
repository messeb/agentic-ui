"""Generative-UI (sandboxed code) tests — approach #4.

The backend only generates code and serves the dataset; execution happens in the browser
sandbox. These tests fake the OpenAI call to verify the structured {status, message, code}.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

from fastapi.testclient import TestClient

import agentic_ui_demo.routers.generative as gen_module
from agentic_ui_demo.config import get_settings
from agentic_ui_demo.routers.generative import DATASET, RESPONSE_SCHEMA


def test_data_endpoint_returns_flights_and_functions(client: TestClient) -> None:
    resp = client.get("/api/generative/data")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["flights"]) == len(DATASET)
    fn_names = {f["name"] for f in body["functions"]}
    assert fn_names == {"loadFlights"}


def test_response_schema_is_strict() -> None:
    assert RESPONSE_SCHEMA["additionalProperties"] is False
    assert set(RESPONSE_SCHEMA["required"]) == set(RESPONSE_SCHEMA["properties"])


def _fake_openai(document: dict):
    class _Completions:
        async def create(self, **_kwargs):
            message = SimpleNamespace(content=json.dumps(document))
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    class _Client:
        def __init__(self, **_kwargs):
            self.chat = SimpleNamespace(completions=_Completions())

    return _Client


def test_generate_returns_code(client: TestClient, monkeypatch) -> None:
    document = {
        "status": "success",
        "message": "A table of flights.",
        "code": "const f = await loadFlights(); document.body.innerHTML = '<table></table>';",
    }
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    get_settings.cache_clear()
    monkeypatch.setattr(gen_module, "AsyncOpenAI", _fake_openai(document))
    try:
        resp = client.post("/api/generative/generate", json={"prompt": "avg price per destination"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert "loadFlights" in body["code"]
    finally:
        get_settings.cache_clear()


def test_generate_requires_key(client: TestClient, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()
    try:
        resp = client.post("/api/generative/generate", json={"prompt": "chart"})
        assert resp.status_code == 503
    finally:
        get_settings.cache_clear()
