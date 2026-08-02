# Agentic UI Demo — developer entrypoints.
# Two standalone apps: backend/ (uv) and frontend/ (pnpm).
# Run `make help` for the list.

.DEFAULT_GOAL := help
.PHONY: help setup dev-backend dev-frontend \
        lint format test typecheck check docker clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

setup: ## Install backend (uv) and frontend (pnpm) deps
	cd backend && uv sync
	cd frontend && corepack enable && pnpm install

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

check: lint test ## Lint + test (what CI runs)

docker: ## Build & run the single-image app on :8080 (reads OPENAI_* from your env)
	docker build -t agentic-ui-patterns .
	docker run --rm -p 8080:8080 -e OPENAI_API_KEY -e OPENAI_MODEL -e OPENAI_BASE_URL agentic-ui-patterns

clean: ## Remove caches and build artifacts
	rm -rf backend/.venv backend/.pytest_cache backend/.ruff_cache backend/htmlcov backend/.coverage \
		frontend/node_modules frontend/.nuxt frontend/.output
