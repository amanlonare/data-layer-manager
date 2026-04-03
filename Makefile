# .PHONY defines targets that are not files
.PHONY: install lint format test dev worker migrate clean help

# Default target
help:
	@echo "Available commands:"
	@echo "  install   - Sync dependencies and setup pre-commit hooks"
	@echo "  lint      - Run Ruff and MyPy checks"
	@echo "  format    - Auto-fix linting and reformat code"
	@echo "  test      - Run all tests with pytest"
	@echo "  dev       - Start the FastAPI development server"
	@echo "  worker    - Start the Celery worker"
	@echo "  migrate   - Apply pending database migrations"
	@echo "  clean     - Remove temporary files and caches"

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
	uv run uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000

worker:
	uv run celery -A apps.worker.main worker --loglevel=info

migrate:
	uv run alembic upgrade head

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -f .coverage
	rm -rf htmlcov
