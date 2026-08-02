"""Approach 3 — Component selection from a catalog (combined with a real booking call).

The model is constrained with OpenAI **Structured Output** to emit a JSON document naming
components from a fixed catalog and supplying their ``props``. A renderer on the frontend
instantiates the real, hand-built components.

Because OpenAI can't combine ``json_schema`` response format with tool calling in one request,
this demo uses the article's **emulation workaround**: the model emits a ``booking_request``
component (its "tool call"). The UI gates it behind a confirm (permission), then a real backend
call books the flight against the **shared state from approach #2** — pulling in any ancillaries
the user added to the shared cart. Ancillary adds are likewise real backend calls.

Model-selectable: ``flight_results``, ``flight_status``, ``ancillary_offer``, ``booking_request``.
System-emitted (rendered, not chosen by the model): ``cart_summary``, ``booking_confirmation``.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException, status
from openai import APIError
from pydantic import BaseModel, Field

from ..config import get_settings
from ..llm import chat_client
from ..tools.flights import add_to_cart, all_flights, book_flight, clear_cart, get_cart, get_flight

router = APIRouter(prefix="/components", tags=["components"])

# --- component prop schemas (strict Structured Output) ------------------------


def _obj(properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(properties),
        "properties": properties,
    }


_FLIGHT = _obj(
    {
        "id": {"type": "string"},
        "origin": {"type": "string"},
        "destination": {"type": "string"},
        "date": {"type": "string"},
        "price": {"type": "number"},
        "seats": {"type": "integer"},
    }
)

_FLIGHT_RESULTS = _obj(
    {
        "origin": {"type": "string"},
        "destination": {"type": "string"},
        "flights": {"type": "array", "items": _FLIGHT},
    }
)

_FLIGHT_STATUS = _obj(
    {
        "flight_id": {"type": "string"},
        "status": {"type": "string", "enum": ["on-time", "delayed", "boarding", "cancelled"]},
        "departure_time": {"type": "string"},
        "gate": {"type": ["string", "null"]},
        "delay_minutes": {"type": ["integer", "null"]},
    }
)

_ANCILLARY_OPTION = _obj(
    {
        "id": {"type": "string"},
        "label": {"type": "string"},
        "description": {"type": "string"},
        "price": {"type": "number"},
        "kind": {
            "type": "string",
            "enum": ["seat", "baggage", "meal", "lounge", "priority", "insurance"],
        },
    }
)

_ANCILLARY_OFFER = _obj(
    {
        "title": {"type": "string"},
        "options": {"type": "array", "items": _ANCILLARY_OPTION},
    }
)

_BOOKING_REQUEST = _obj({"flight_id": {"type": "string"}, "passenger": {"type": "string"}})

# Components the model may choose via Structured Output.
CATALOG: list[dict[str, Any]] = [
    {
        "name": "flight_results",
        "description": "A list of flights matching a search, one card per flight.",
        "props": _FLIGHT_RESULTS,
    },
    {
        "name": "flight_status",
        "description": "Live status for one flight (on-time/delayed/boarding/cancelled).",
        "props": _FLIGHT_STATUS,
    },
    {
        "name": "ancillary_offer",
        "description": "Upsell options such as a better seat, extra baggage, meals, lounge access.",
        "props": _ANCILLARY_OFFER,
    },
    {
        "name": "booking_request",
        "description": "A confirm card to BOOK a flight for a passenger (user must confirm).",
        "props": _BOOKING_REQUEST,
    },
]


def _component_schema(entry: dict[str, Any]) -> dict[str, Any]:
    return _obj({"component": {"type": "string", "const": entry["name"]}, "props": entry["props"]})


RESPONSE_SCHEMA: dict[str, Any] = _obj(
    {
        "message": {"type": "string"},
        "components": {
            "type": "array",
            "items": {"anyOf": [_component_schema(entry) for entry in CATALOG]},
        },
    }
)


def _build_system_prompt() -> str:
    return (
        "You are a flight assistant that answers by SELECTING UI components from a catalog and "
        "filling their props — never with plain prose alone. Always return a short `message` "
        "plus the `components` that best answer the request.\n\n"
        "Catalog:\n"
        "- flight_results: when the user searches flights. Fill `flights` from the DATA below.\n"
        "- flight_status: when the user asks about a flight's status. Invent a plausible "
        "departure_time/gate; set delay_minutes when status is 'delayed'.\n"
        "- ancillary_offer: when the user wants extras (better seat, more baggage, meal, lounge). "
        "Offer 2-4 relevant options with realistic EUR prices.\n"
        "- booking_request: when the user wants to BOOK a specific flight AND has given a "
        "passenger name. Fill flight_id and passenger. If no name was given, ask for it in "
        "`message` and do NOT emit booking_request. Never claim a booking succeeded yourself — "
        "the booking only happens after the user confirms.\n\n"
        f"DATA (available flights): {json.dumps(all_flights())}"
    )


class ComponentChatRequest(BaseModel):
    messages: list[dict[str, Any]] = Field(min_length=1)


class AncillaryAddRequest(BaseModel):
    id: str
    label: str
    description: str
    price: float
    kind: str


class BookRequest(BaseModel):
    flight_id: str
    passenger: str = Field(min_length=1)


def _cart_summary_doc(message: str) -> dict[str, Any]:
    items = get_cart()
    subtotal = sum(o["price"] for o in items)
    return {
        "message": message,
        "components": [
            {"component": "cart_summary", "props": {"items": items, "subtotal": subtotal}}
        ],
    }


@router.get("", summary="List the component catalog")
def list_catalog() -> dict[str, Any]:
    return {
        "components": [
            {"name": c["name"], "description": c["description"], "props": c["props"]}
            for c in CATALOG
        ]
    }


@router.post("/chat", summary="Select components via Structured Output")
async def component_chat(req: ComponentChatRequest) -> dict[str, Any]:
    settings = get_settings()
    if not settings.openai_api_key:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "OPENAI_API_KEY is not set on the server. Set it and restart the backend.",
        )

    client = chat_client()
    messages = [{"role": "system", "content": _build_system_prompt()}]
    messages += [m for m in req.messages if m.get("role") != "system"]

    try:
        resp = await client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "ui_document", "strict": True, "schema": RESPONSE_SCHEMA},
            },
        )
    except APIError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"OpenAI error: {exc.message}") from exc

    content = resp.choices[0].message.content or "{}"
    return json.loads(content)


@router.post("/ancillary", summary="Add an ancillary to the cart (real action)")
def add_ancillary(req: AncillaryAddRequest) -> dict[str, Any]:
    add_to_cart(req.model_dump())
    return _cart_summary_doc(f"Added “{req.label}” to your cart.")


@router.post("/book", summary="Book a flight with the cart's ancillaries (real action)")
def book(req: BookRequest) -> dict[str, Any]:
    result = book_flight(req.flight_id, req.passenger)
    if "error" in result:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, result["error"])

    flight = get_flight(req.flight_id)
    base_price = float(flight["price"])
    extras = [{"label": o["label"], "price": o["price"]} for o in get_cart()]
    total = base_price + sum(e["price"] for e in extras)
    clear_cart()

    props = {
        "booking_id": result["booking_id"],
        "flight_id": req.flight_id,
        "passenger": req.passenger,
        "base_price": base_price,
        "extras": extras,
        "total": total,
    }
    return {
        "message": f"Booked {req.flight_id} for {req.passenger}.",
        "components": [{"component": "booking_confirmation", "props": props}],
    }
