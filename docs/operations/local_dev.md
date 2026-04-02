# Local Development Workflow

`data-layer-manager` uses **`uv`** for dependency management, virtual environments, and tool execution. Leveraging `uv` ensures faster sync times and reproducible environments.

## Setup

1.  **Install dependencies**:
    ```bash
    uv sync
    ```
2.  **Initialize pre-commit hooks**:
    ```bash
    uv run pre-commit install
    ```
3.  **Environment Variables**:
    Copy `.env.example` to `.env` and configure accordingly.

## Daily Workflow

### Synchronizing Your Local Environment
Always run `uv sync` after pulling changes from the repository.
```bash
uv sync
```

### Running the API
Use the `dev` command to start the FastAPI server with auto-reload.
```bash
uv run uvicorn apps.api.src.main:app --reload
```

### Running the Worker
Start the Celery worker for the `ingestion` queue.
```bash
uv run celery -A apps.worker.src.main worker -Q ingestion --loglevel=info
```

## Quality Control

### Manual Linting & Formatting
We recommend running these commands before committing:
```bash
# Full Ruff check
uv run ruff check . --fix

# Full Type check
uv run mypy .
```

### Running Tests
Execute the full test suite with `pytest`.
```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=src/data_layer_manager
```

## Documentation

-   **Update Design**: If modifying core architecture, update the relevant **[Architecture Overview](../architecture/overview.md)** or create a new **ADR**.
-   **Style**: Use **Google-style docstrings** for all new technical implementations.
