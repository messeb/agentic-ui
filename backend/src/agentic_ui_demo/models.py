"""Pydantic models mirroring the shared approaches manifest."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class Maturity(StrEnum):
    proven = "proven"
    established = "established"
    emerging = "emerging"
    paused = "paused"
    least_mature = "least-mature"


class Status(StrEnum):
    not_implemented = "not-implemented"
    in_progress = "in-progress"
    implemented = "implemented"


class Approach(BaseModel):
    """One of the 8 Agentic UI approaches (a scaffolded starting point)."""

    id: str
    number: int = Field(ge=1, le=8)
    title: str
    tagline: str
    input: str
    output: str
    how_it_works: str = Field(alias="howItWorks")
    what_you_need: list[str] = Field(alias="whatYouNeed")
    agentic_level: int = Field(alias="agenticLevel", ge=0, le=5)
    maturity: Maturity
    status: Status

    model_config = {"populate_by_name": True}


class Manifest(BaseModel):
    version: str
    description: str = ""
    approaches: list[Approach]


class DemoNotImplemented(BaseModel):
    """Response body returned by every not-yet-implemented approach demo."""

    approach_id: str
    status: Status = Status.not_implemented
    message: str
    next_step: str
