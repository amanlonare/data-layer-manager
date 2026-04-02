# ADR 0001: Library-First Design

## Status
Accepted

## Context
The `data-layer-manager` is designed to be the foundational data backbone for multiple independent systems (Knowledge Search, Copilot Platform, Automation Agents). These systems will have different transport requirements:
-   **Knowledge Search**: Synchronous REST API for low-latency retrieval.
-   **Copilot Platform**: REST and GraphQL APIs.
-   **Automation Agents**: MCP (Model Context Protocol) tools.
-   **Worker Processes**: Celery-based background ingestion.

## Decision
We will develop the core logic as a standalone, reusable Python library located in `src/data_layer_manager/`. This library should contain all domain logic, interface definitions, and infrastructure implementations.

-   **Library Responsibility**: Business logic, database interactions, vector store clients, parsing, chunking, and embeddings.
-   **Application Responsibility**: Transport configuration, routing, middleware, request validation, authentication, and dependency injection "wiring" (fastapi, mcp, worker).

## Consequences
-   **Pros**:
    -   High reusability across entrypoints.
    -   Reduced risk of business logic leaking into HTTP handlers.
    -   Easier to migrate between frameworks (e.g., FastAPI to something else).
-   **Cons**:
    -   Slightly more boilerplate for dependency injection and repository setup.
    -   Requires clear boundaries to avoid leaking "presentation" details into the library.
