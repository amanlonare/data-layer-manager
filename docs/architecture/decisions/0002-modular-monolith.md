# ADR 0002: Modular Monolith

## Status
Accepted

## Context
The project needs to support multiple independent capabilities:
-   **Ingestion**: Processing of external files/data.
-   **Retrieval**: Locating and fetching relevant chunks for query.
-   **Persistence**: Long-term storage of document and job metadata.
-   **Vector Search**: Semantic query matching.

The current team size and velocity requirements favor a unified codebase, but the long-term goal is to have the flexibility to decouple these components.

## Decision
We will use a **Modular Monolith** structure within `src/data_layer_manager/`.
Modules are organized as subdirectories such as `domain`, `application`, and `infrastructure`.

-   **Domain Layer**: Core entities and business logic (e.g., IngestionJob, Document, Chunk).
-   **Application Layer**: Use cases and orchestrators (e.g., IngestFileUseCase, RetrieveRelevantChunksUseCase).
-   **Infrastructure Layer**: Implementation details (e.g., SQLAlchemyDocumentRepository, QdrantVectorStore).

## Consequences
-   **Pros**:
    -   Consolidated source of truth for dependencies.
    -   Reduced dev-ops overhead compared to microservices.
    -   Faster development and cross-module refactoring.
-   **Cons**:
    -   Risk of "spaghetti" logic if boundaries aren't strictly enforced.
    -   Binary/deployment scaling is limited to a single artifact.
-   **Mitigation**: Use strict typing and enforce interface-based boundaries to ensure modules remain decoupled.
