# data-layer-manager

**Library-first, Modular Monolith backend for modern AI Knowledge Systems.**

`data-layer-manager` is the reusable data layer for enterprise AI systems. It connects multiple data sources, extracts and cleans text, chunks documents, generates embeddings, and retrieves relevant context with citation-ready metadata.

---

## 🚀 Vision

- **Knowledge Hub**: Centralized RAG for enterprise search.
- **Agent Platform**: Foundational data layer for internal copilots and automation agents.
- **Enterprise Ready**: Production-grade observability, telemetry, and security.

## 🏗️ Architecture

Following the **Modular Monolith** and **Library-First** principles:

- **Core Package**: `src/data_layer_manager/` (Domain logic, Infrastructure, Application logic).
- **App Entrypoints**:
  - `apps/api/`: Thin FastAPI layer for transport.
  - `apps/worker/`: Celery/Queue-based background processing for long-running ingestion/indexing jobs.
  - `apps/mcp/`: Model Context Protocol server for direct AI tool integration.

### Background Processing

We use **Celery** with **Redis** as a broker to handle resource-intensive tasks asynchronously. The system is designed with separate queues for optimized resource allocation:
- **`ingestion`**: Parsing, cleaning, and embedding large-scale data.
- **`maintenance`**: Reindexing, cleanup, and cache management.

Refer to the **[Celery Task Boundary Design](./docs/architecture/celery_tasks.md)** for more details.

### Project Quality

- **Linting & Formatting**: Enforced via **Ruff** in the pre-commit stage.
- **Static Analysis**: **Mypy** is used for strict type checking in the CI/CD pipeline.
- **Security**: **Snyk** integration for vulnerability scanning at each PR.

Refer to the **[Quality Policy](./docs/operations/quality_policy.md)** for detailed standards.

## 🛠️ Technology Stack

- **Core**: Python 3.11+, [uv](https://github.com/astral-sh/uv)
- **Framework**: FastAPI (API), Celery (Background Jobs)
- **Models**: Pydantic v2
- **Database**: SQLAlchemy 2.x, Alembic
- **Vector Stores**: pgvector (PostgreSQL), Qdrant
- **Observability**: Structured Logging, Telemetry, Health checks

## 📂 Repository Structure

```text
data-layer-manager/
├── apps/               # Entrypoints (API, Worker, MCP)
├── src/                # Core library source
│   └── data_layer_manager/
│       ├── core/       # Global config, logging, telemetry
│       ├── domain/     # Entities, Interfaces, Services (The "What")
│       ├── application/# Use cases, Orchestrators (The "How")
│       └── infrastructure/ # DB, VectorStores, Celery, Connectors (The "Tools")
├── docs/               # Architecture, ADRs, Operational guides
├── tests/              # Unit, Integration, E2E tests
└── scripts/            # Dev, Ops, and Evaluation utilities
```

## 🚥 Local Development

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv)

### Setup
```bash
uv sync
```

## 📜 Contributing
Refer to `CONTRIBUTING.md` (to be created) for details on our coding standards and PR workflow.
