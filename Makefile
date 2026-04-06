# .PHONY defines targets that are not files
.PHONY: install lint format test dev worker mcp migrate clean help services-up services-down services-reset db-init smoke-test

# Default target
help:
	@echo "Available commands:"
	@echo "  install        - Sync dependencies and setup pre-commit hooks"
	@echo "  lint           - Run Ruff and MyPy checks"
	@echo "  format         - Auto-fix linting and reformat code"
	@echo "  test           - Run all tests with pytest"
	@echo "  dev            - Start the FastAPI development server"
	@echo "  worker         - Start the Celery worker"
	@echo "  mcp            - Start the MCP server for AI tools"
	@echo "  migrate        - Apply pending database migrations"
	@echo "  clean          - Remove temporary files and caches"
	@echo ""
	@echo "Infrastructure commands:"
	@echo "  services-up    - Start backend services (Postgres, Neo4j, Qdrant, Redis)"
	@echo "  services-down  - Stop backend services"
	@echo "  services-reset - Destructive reset: wipe volumes and restart"
	@echo "  db-init        - Setup .env (if missing) and run migrations"
	@echo "  smoke-test     - Run automated backend connectivity check"

install:
	uv sync --all-extras
	uv run pre-commit install

lint:
	uv run ruff check .
	uv run mypy .

format:
	uv run ruff check --fix .
	uv run ruff format .

test:
	uv run pytest tests/ --asyncio-mode=auto --cov=data_layer_manager

dev:
	uv run uvicorn data_layer_manager.interfaces.api.app:app --reload --host 0.0.0.0 --port 8000

worker:
	uv run celery -A apps.worker.main worker --loglevel=info

mcp:
	@PYTHONPATH=. uv run python -m apps.mcp.src.main

migrate:
	uv run alembic upgrade head

services-up:
	docker compose up -d

services-down:
	docker compose down

services-reset:
	docker compose down -v
	docker compose up -d
	@echo "Waiting for services to boot..."
	@sleep 5
	$(MAKE) migrate

db-init:
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env from .env.example"; fi
	@echo "Waiting for Postgres to be ready..."
	@sleep 3
	$(MAKE) migrate

smoke-test:
	PYTHONPATH=. uv run python scripts/smoke_check.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -f .coverage
	rm -rf htmlcov
