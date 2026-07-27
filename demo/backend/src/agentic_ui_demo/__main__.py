"""`agentic-ui-demo` console entry point."""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    uvicorn.run(
        "agentic_ui_demo.main:app",
        host=os.getenv("DEMO_HOST", "0.0.0.0"),
        port=int(os.getenv("DEMO_PORT", "8000")),
        reload=os.getenv("DEMO_RELOAD", "true").lower() == "true",
    )


if __name__ == "__main__":
    main()
