# Project Architecture Guide

This project follows **Clean Architecture** principles, ensuring a clear separation between business logic and infrastructure.

## 🏗️ Layer Dependency Diagram
The most critical rule is that **dependencies always point inward**. The Domain layer never knows about the database or external APIs.

```mermaid
flowchart TD
    subgraph Presentation ["Presentation (Access)"]
        CLI[CLI Tools]
        API[FastAPI REST Support]
    end

    subgraph Application ["Application (Use Cases)"]
        UC[Ingest & Search Orchestration]
    end

    subgraph Infrastructure ["Infrastructure (Technical)"]
        DB[(Postgres + SQLAlchemy)]
        VS[(pgvector Search Engine)]
        REPO[Concrete Repositories]
    end

    subgraph Domain ["Domain (The Core)"]
        ENT[Entities: Document & Chunk]
        INT[Interfaces: Repository / Vector]
    end

    %% Dependency Flow (Points Inward)
    CLI --> UC
    API --> UC
    UC --> ENT
    UC --> INT

    %% Implementation Implementation
    REPO -.-> INT
    REPO --- DB
    REPO --- VS
```

## 📂 Directory to Layer Mapping

| Directory | Layer | Purpose |
| :--- | :--- | :--- |
| `data_layer_manager/domain/` | **Core** | Pure logic, entities, and repository interfaces. |
| `data_layer_manager/application/` | **Use Case** | Coordinates the workflow between domain and infra. |
| `data_layer_manager/infrastructure/` | **Adapter** | Concrete database models and repository implementations. |
| `data_layer_manager/presentation/` | **Gateway** | How the user (human or machine) triggers the app. |
