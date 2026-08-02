"""Component-selection tests (approach #3).

Validates the catalog, the strict Structured Output schema, and the endpoint with a faked
OpenAI client (which returns a JSON document just like a real structured-output call).
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import agentic_ui_demo.routers.components as comp_module
from agentic_ui_demo.config import get_settings
from agentic_ui_demo.routers.components import CATALOG, RESPONSE_SCHEMA
from agentic_ui_demo.tools import reset_state


@pytest.fixture(autouse=True)
def _fresh_state():
    reset_state()
    yield
    reset_state()


def test_catalog_lists_model_components(client: TestClient) -> None:
    resp = client.get("/api/components")
    assert resp.status_code == 200
    names = {c["name"] for c in resp.json()["components"]}
    assert names == {"flight_results", "flight_status", "ancillary_offer", "booking_request"}


def test_add_ancillary_then_book_includes_extras(client: TestClient) -> None:
    add = client.post(
        "/api/components/ancillary",
        json={
            "id": "seat_xl",
            "label": "Extra legroom",
            "description": "Exit row",
            "price": 25,
            "kind": "seat",
        },
    )
    assert add.status_code == 200
    summary = add.json()["components"][0]
    assert summary["component"] == "cart_summary"
    assert summary["props"]["subtotal"] == 25

    booked = client.post("/api/components/book", json={"flight_id": "AB123", "passenger": "Alice"})
    assert booked.status_code == 200
    conf = booked.json()["components"][0]
    assert conf["component"] == "booking_confirmation"
    props = conf["props"]
    assert props["base_price"] == 149
    assert props["extras"] == [{"label": "Extra legroom", "price": 25}]
    assert props["total"] == 174

    # Cart is cleared after booking, and the seat was decremented in shared state.
    from agentic_ui_demo.tools.flights import get_cart, get_flight

    assert get_cart() == []
    assert get_flight("AB123")["seats"] == 3


def test_book_sold_out_returns_400(client: TestClient) -> None:
    resp = client.post("/api/components/book", json={"flight_id": "CD201", "passenger": "Bob"})
    assert resp.status_code == 400


def test_response_schema_is_strict() -> None:
    # Every object in a strict Structured Output schema must forbid extra keys and
    # list all properties as required.
    def check(node: dict) -> None:
        if node.get("type") == "object":
            assert node["additionalProperties"] is False
            assert set(node["required"]) == set(node["properties"])
            for child in node["properties"].values():
                check(child)
        if node.get("type") == "array":
            check(node["items"])
        for branch in node.get("anyOf", []):
            check(branch)

    check(RESPONSE_SCHEMA)


def _fake_openai(document: dict):
    class _Completions:
        async def create(self, **_kwargs):
            message = SimpleNamespace(content=json.dumps(document))
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    class _Client:
        def __init__(self, **_kwargs):
            self.chat = SimpleNamespace(completions=_Completions())

    return _Client


def test_component_chat_returns_document(client: TestClient, monkeypatch) -> None:
    document = {
        "message": "Here are your flights.",
        "components": [
            {
                "component": "flight_results",
                "props": {
                    "origin": "Graz",
                    "destination": "Hamburg",
                    "flights": [
                        {
                            "id": "AB123",
                            "origin": "Graz",
                            "destination": "Hamburg",
                            "date": "2026-08-01",
                            "price": 149,
                            "seats": 4,
                        }
                    ],
                },
            }
        ],
    }
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    get_settings.cache_clear()
    monkeypatch.setattr(comp_module, "AsyncOpenAI", _fake_openai(document))
    try:
        resp = client.post(
            "/api/components/chat",
            json={"messages": [{"role": "user", "content": "flights Graz to Hamburg"}]},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["components"][0]["component"] == "flight_results"
        assert body["components"][0]["props"]["flights"][0]["id"] == "AB123"
    finally:
        get_settings.cache_clear()


def test_component_chat_requires_key(client: TestClient, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()
    try:
        resp = client.post(
            "/api/components/chat", json={"messages": [{"role": "user", "content": "hi"}]}
        )
        assert resp.status_code == 503
    finally:
        get_settings.cache_clear()


def test_catalog_names_used_in_schema() -> None:
    consts = {
        b["properties"]["component"]["const"]
        for b in RESPONSE_SCHEMA["properties"]["components"]["items"]["anyOf"]
    }
    assert consts == {c["name"] for c in CATALOG}
