"""Loads and caches the shared approaches manifest."""

from __future__ import annotations

import json
from functools import lru_cache

from .config import get_settings
from .models import Approach, Manifest


@lru_cache
def load_manifest() -> Manifest:
    """Read and validate the shared approaches manifest (cached)."""
    path = get_settings().approaches_manifest
    if not path.exists():
        raise FileNotFoundError(
            f"Approaches manifest not found at {path}. "
            "Set DEMO_APPROACHES_MANIFEST to the path of shared/approaches.json."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    return Manifest.model_validate(data)


def list_approaches() -> list[Approach]:
    return load_manifest().approaches


def get_approach(approach_id: str) -> Approach | None:
    return next((a for a in list_approaches() if a.id == approach_id), None)
