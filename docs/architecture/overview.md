# Architecture Overview

`data-layer-manager` is designed as a **Library-First Modular Monolith**. The core business logic and infrastructure are defined in a reusable Python package (`src/data_layer_manager/`), which is then imported and utilized by various application entrypoints (`apps/`).

## Core Architecture Design Principles

1.  **Separation of Concerns**: We use the layering of **Domain**, **Application**, and **Infrastructure**.
    -   **Domain**: Defines "the what" — Entities, Value Objects, and abstract interfaces.
    -   **Application**: Defines "the how" — Use cases, logic orchestration, and DTOs.
    -   **Infrastructure**: Implementation details — Vector Stores, Celery Tasks, Persistence, Connectors.
    -   **Presentation**: Thin mappers for external consumption (API/MCP).

2.  **Modular Modular Monolith**: Each core capability (e.g., Ingestion, Retrieval, Parsing) is a module within the library. The code should be organized so that if it grows too large, it could be split into microservices, but for now, it remains a single deployment unit.

3.  **Library-First**: The core library contains *no* transport logic (routes, schemas, middlewares). These are handled by the apps in `apps/`.

## Data Flow: Ingestion Pipeline

The ingestion pipeline is designed to be **asynchronous** for large-scale data processing.

1.  **API Call**: `POST /ingestion/jobs` triggers a record creation.
2.  **Task Producer**: The API worker pushes a job to the Celery queue.
3.  **Celery Worker**: Performs parsing, cleaning, chunking, and embedding.
4.  **Vector Store**: New knowledge is stored.
5.  **Status Sync**: Job status is updated in the persistence layer.

## Data Flow: Retrieval Pipeline

The retrieval pipeline is optimized for **low-latency** synchronous queries.

1.  **API Call**: `POST /retrieval/query`.
2.  **Embedder**: Query is embedded in-memory or via remote API.
3.  **Vector Search**: Query is matched against vectors (pgvector or Qdrant).
4.  **Reranking (Optional)**: Results are refined.
5.  **Response**: Relevant chunks are returned with citation-ready metadata.

## Service Map

| Component | Responsibility | Provider-Pluggable? |
| :--- | :--- | :--- |
| **Parsers** | Extracting text from files (PDF/DOCX) | Yes |
| **Cleaners** | Normalizing text and removing boilerplate | Yes |
| **Chunkers** | Splitting text based on context | Yes |
| **Embedders** | Generating 1536/3072d vectors | Yes |
| **Vector Store** | Storing and retrieving vectors | Yes (pgvector/Qdrant) |
| **Connectors** | Syncing data from external sources (S3/S3/Notion) | Yes |

## Technology Choices

Refer to the [ADRs](./decisions/) for detailed decision records.
