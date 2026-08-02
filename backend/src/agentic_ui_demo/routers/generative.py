"""Approach 4 — Generative UI via sandboxed code.

The model does not compute; it *describes* the computation as a small JavaScript snippet that
runs in a locked-down browser sandbox (opaque-origin iframe, strict CSP, no network, no DOM
access to the host). The snippet may call only two whitelisted runtime functions, bridged to
the host via ``postMessage``:

- ``loadFlights()``  — data source: returns the flight dataset below.
- ``generateChart({title, data})`` — sink: the host renders a bar chart.

The backend only *generates* the code (OpenAI Structured Output) and serves the dataset that
backs ``loadFlights``. It never executes the generated code.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException, status
from openai import APIError, AsyncOpenAI
from pydantic import BaseModel, Field

from ..config import get_settings

router = APIRouter(prefix="/generative", tags=["generative"])

# --- dataset backing loadFlights() -------------------------------------------

DATASET: list[dict[str, Any]] = [
    {
        "id": "AB123",
        "origin": "Graz",
        "destination": "Hamburg",
        "date": "2026-08-01",
        "price": 149,
        "delay_minutes": 0,
    },
    {
        "id": "AB124",
        "origin": "Graz",
        "destination": "Hamburg",
        "date": "2026-08-01",
        "price": 119,
        "delay_minutes": 35,
    },
    {
        "id": "AB125",
        "origin": "Graz",
        "destination": "Hamburg",
        "date": "2026-08-02",
        "price": 129,
        "delay_minutes": 0,
    },
    {
        "id": "CD200",
        "origin": "Vienna",
        "destination": "Berlin",
        "date": "2026-08-01",
        "price": 99,
        "delay_minutes": 10,
    },
    {
        "id": "CD201",
        "origin": "Vienna",
        "destination": "Berlin",
        "date": "2026-08-02",
        "price": 135,
        "delay_minutes": 0,
    },
    {
        "id": "CD202",
        "origin": "Vienna",
        "destination": "Berlin",
        "date": "2026-08-02",
        "price": 115,
        "delay_minutes": 60,
    },
    {
        "id": "EF300",
        "origin": "Graz",
        "destination": "London",
        "date": "2026-08-01",
        "price": 210,
        "delay_minutes": 0,
    },
    {
        "id": "EF301",
        "origin": "Graz",
        "destination": "London",
        "date": "2026-08-03",
        "price": 189,
        "delay_minutes": 20,
    },
    {
        "id": "GH400",
        "origin": "Vienna",
        "destination": "Paris",
        "date": "2026-08-01",
        "price": 175,
        "delay_minutes": 0,
    },
    {
        "id": "GH401",
        "origin": "Vienna",
        "destination": "Paris",
        "date": "2026-08-03",
        "price": 160,
        "delay_minutes": 45,
    },
]

# Human/LLM-readable description of the runtime functions the sandbox exposes.
RUNTIME_FUNCTIONS: list[dict[str, Any]] = [
    {
        "name": "loadFlights",
        "kind": "data source",
        "signature": "loadFlights(): Promise<Flight[]>",
        "description": "Returns all flights. Flight = {id, origin, destination, date (YYYY-MM-DD), "
        "price (EUR number), delay_minutes (number)}.",
    },
]

SYSTEM_PROMPT = (
    "You write a short snippet of plain async JavaScript (a function BODY, no wrapper) that runs "
    "in a locked, isolated sandbox iframe and RENDERS UI directly into document.body.\n"
    "Available: loadFlights(): Promise<Flight[]>, Flight = {id, origin, destination, "
    "date 'YYYY-MM-DD', price (EUR number), delay_minutes (number)}.\n\n"
    "Rules:\n"
    "- First `await loadFlights()`, then build the visualization the user asked for by creating "
    "DOM: set document.body.innerHTML, or use createElement / inline SVG.\n"
    "- Pick the format that best communicates the answer and VARY it across requests: a table, a "
    "bar or pie chart (inline SVG or styled divs), cards, a grid, or a compact summary. Be "
    "creative and make it look clean with inline CSS.\n"
    "- Use ONLY loadFlights and the DOM. NEVER use fetch, network, imports/require, timers, "
    "external URLs or resources. Images only as data: URIs.\n"
    "- Self-contained and readable. No markdown fences, no function wrapper.\n\n"
    "Return status 'success' with a one-line message describing what you rendered, or status "
    "'error' if it cannot be done with this data.\n\n"
    f"Example dataset row: {json.dumps(DATASET[0])}"
)

RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["status", "message", "code"],
    "properties": {
        "status": {"type": "string", "enum": ["success", "error"]},
        "message": {"type": "string"},
        "code": {"type": "string"},
    },
}


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1)


@router.get("/data", summary="Dataset + runtime function descriptions")
def get_data() -> dict[str, Any]:
    return {"flights": DATASET, "functions": RUNTIME_FUNCTIONS}


@router.post("/generate", summary="Generate sandboxed code (Structured Output)")
async def generate(req: GenerateRequest) -> dict[str, Any]:
    settings = get_settings()
    if not settings.openai_api_key:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "OPENAI_API_KEY is not set on the server. Export it and restart the backend.",
        )

    client = AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url or None)
    try:
        resp = await client.chat.completions.create(
            model=settings.openai_model,
            temperature=0.9,  # more varied UI across requests
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": req.prompt},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "generated_code",
                    "strict": True,
                    "schema": RESPONSE_SCHEMA,
                },
            },
        )
    except APIError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"OpenAI error: {exc.message}") from exc

    return json.loads(resp.choices[0].message.content or "{}")
