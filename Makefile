# Agentic UI Demo — developer entrypoints.
# Two standalone apps: backend/ (uv) and frontend/ (pnpm).
# Run `make help` for the list.

.DEFAULT_GOAL := help
.PHONY: help setup sync-manifest check-manifest dev-backend dev-frontend \
        lint format test typecheck check docker-up docker-down clean

MANIFEST := shared/approaches.json
BACKEND_MANIFEST := backend/src/agentic_ui_demo/data/approaches.json
FRONTEND_MANIFEST := frontend/shared/approaches.json

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

setup: sync-manifest ## Install backend (uv) and frontend (pnpm) deps
	cd backend && uv sync
	cd frontend && corepack enable && pnpm install

sync-manifest: ## Copy the canonical manifest into both standalone apps
	cp $(MANIFEST) $(BACKEND_MANIFEST)
	cp $(MANIFEST) $(FRONTEND_MANIFEST)
	@echo "synced $(MANIFEST) -> backend & frontend"

check-manifest: ## Fail if the vendored manifests drift from the canonical one
	@diff -q $(MANIFEST) $(BACKEND_MANIFEST)  >/dev/null || { echo "backend manifest out of sync — run 'make sync-manifest'"; exit 1; }
	@diff -q $(MANIFEST) $(FRONTEND_MANIFEST) >/dev/null || { echo "frontend manifest out of sync — run 'make sync-manifest'"; exit 1; }
	@echo "manifests in sync"

dev-backend: ## Run the FastAPI backend with reload
	cd backend && uv run uvicorn agentic_ui_demo.main:app --reload --port 8000

dev-frontend: ## Run the Nuxt dev server
	cd frontend && pnpm run dev

lint: ## Lint Python (ruff) and frontend (eslint)
	cd backend && uv run ruff check .
	cd frontend && pnpm run lint

format: ## Auto-format Python
	cd backend && uv run ruff format . && uv run ruff check --fix .

test: ## Run backend tests with coverage
	cd backend && uv run pytest --cov

typecheck: ## Type-check the frontend
	cd frontend && pnpm run typecheck

check: check-manifest lint test ## Manifest sync + lint + test (what CI runs)

docker-up: ## Build & start the full stack
	docker compose up --build

docker-down: ## Stop the stack
	docker compose down

clean: ## Remove caches and build artifacts
	rm -rf backend/.venv backend/.pytest_cache backend/.ruff_cache backend/htmlcov backend/.coverage \
		frontend/node_modules frontend/.nuxt frontend/.output
