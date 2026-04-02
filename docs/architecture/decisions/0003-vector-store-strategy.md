# ADR 0003: Vector Store Strategy

## Status
Accepted

## Context
We need a robust, scalable way to store and retrieve high-dimensional embeddings (vectors). The system must support flexible local storage for development and enterprise-grade performance for production.

## Decision
We will implement a **Multi-Adapter Vector Store Strategy**, supporting both **pgvector** and **Qdrant** for the MVP.

1.  **pgvector**: Recommended for development and integrated hybrid-search scenarios where a single relational database (PostgreSQL) is preferred for both metadata and vectors.
2.  **Qdrant**: Recommended for high-scale retrieval and production environments requiring specialized vector search optimizations.
3.  **Interface based**: Define a `VectorStoreRepository` interface in the domain/infrastructure layers. Use a factory to switch between implementations based on configuration.

## Consequences
-   **Pros**:
    -   Flexibility to change providers based on infrastructure constraints.
    -   Unified metadata filtering API across different vector databases.
    -   Ability to test with a lightweight (e.g., in-memory) implementation.
-   **Cons**:
    -   Complexity in ensuring feature parity across filtered search in different vector databases.
    -   Maintenance of multiple database adapters.
-   **Mitigation**: Implement common query mapping in the infrastructure layer to mask differences between pgvector and Qdrant APIs.
