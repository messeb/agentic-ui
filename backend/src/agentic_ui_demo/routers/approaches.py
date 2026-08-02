"""Approach endpoints.

Metadata is served from the shared manifest. The per-approach `demo` endpoint is a
deliberate stub: it returns HTTP 501 so the frontend can wire up the full flow while
each approach stays unimplemented. This is where you plug in real logic.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from ..models import Approach, DemoNotImplemented
from ..registry import get_approach, list_approaches

router = APIRouter(prefix="/approaches", tags=["approaches"])


@router.get("", summary="List all 8 approaches")
def get_approaches() -> list[Approach]:
    return list_approaches()


@router.get("/{approach_id}", summary="Get one approach")
def get_one(approach_id: str) -> Approach:
    approach = get_approach(approach_id)
    if approach is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Unknown approach: {approach_id}")
    return approach


@router.api_route(
    "/{approach_id}/demo",
    methods=["GET", "POST"],
    summary="Run an approach demo (stub — returns 501)",
    responses={501: {"model": DemoNotImplemented}},
)
def run_demo(approach_id: str) -> JSONResponse:
    """Entry point for each approach's live demo.

    Intentionally unimplemented. To bring an approach to life, replace this branch
    with the real handler (stream tokens, dispatch tool calls, render components, ...).
    """
    approach = get_approach(approach_id)
    if approach is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Unknown approach: {approach_id}")

    body = DemoNotImplemented(
        approach_id=approach.id,
        message=f"The '{approach.title}' demo is not implemented yet — this is the starting point.",
        next_step=(
            "Implement the handler in "
            "backend/src/agentic_ui_demo/routers/approaches.py::run_demo and the matching "
            f"frontend page frontend/pages/approaches/{approach.id}.vue."
        ),
    )
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, content=body.model_dump(mode="json")
    )
