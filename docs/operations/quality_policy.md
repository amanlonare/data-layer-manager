# Repository Quality Policy

`data-layer-manager` maintains a high standard of code quality through automated checks, rigorous linting, and comprehensive documentation.

## Automated Quality Checks

We use **`pre-commit`** for local verification before changes are committed.

### Pre-commit Configuration
-   **Ruff**: Handles formatting (`black` compatible) and linting.
-   **Security**: Scans for secrets and insecure coding patterns.
-   **Docstring Consistency**: Ensures standard Google-style documentation.

### Gating Strategy
-   **Local Gating**: `ruff format` and `ruff check` MUST pass for a commit to succeed.
-   **CI Gating**: **Mypy** (static typing) and **Snyk** (security) are run in the GitHub Actions pipeline. Failed typing or high-severity security issues will block the PR.

## Code Standards

### Formatting & Linting
-   Follow **PEP 8**.
-   Max line length: **88 characters** (Ruff default).
-   Strict imports: Use **`ruff select = ["I"]`** for organized imports.

### Typing
-   All new code MUST be fully typed using **Python 3.11+ type hints**.
-   Avoid **`Any`**; use `Protocols` or `Generics` where appropriate.
-   Pydantic v2 models are the standard for all data validation.

## Documentation Standards

### Docstrings
All public functions, classes, and modules MUST include Google-style docstrings.

```python
def ingest_document(file_path: Path, source_id: str) -> str:
    """Ingests a local file into the data layer.

    Args:
        file_path: The absolute path to the document.
        source_id: The unique identifier for the data source.

    Returns:
        The generated job_id for tracking ingestion status.

    Raises:
        FileNotFoundError: If the document doesn't exist.
    """
```

### Architecture Updates
Any change that alters module boundaries or introduces new infrastructure dependencies MUST be accompanied by an update to the **Architecture Overview** or a new **ADR**.
