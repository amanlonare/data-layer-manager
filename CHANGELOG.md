# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.5] - 2026-04-05

### Added
- **FastAPI Core**: A production-ready API layer with unified `search` (hybrid/graph) and `ingest` (text/upload) endpoints.
- **MCP Server Implementation**: A standalone Model Context Protocol server enabling tool-based knowledge retrieval for LLM ecosystems (e.g., Claude/Claude Code).
- **OpenAI Embedding Engine**: Integrated support for OpenAI's `text-embedding-3` models with configurable batch processing.
- **Neo4j Hybrid Search**: Integrated the graph-based retriever into the parallel retrieval pipeline for relationship-aware search.
- **Dockerized Infrastructure**: A unified `docker-compose.yml` for PostgreSQL (pgvector), Qdrant, and Neo4j for seamless local development and staging orchestration.

### Changed
- **Dynamic Vector Dimensions**: Updated database schema and pgvector integration to support dynamic embedding dimensions, removing hard-coded limitations.

## [0.0.4] - 2026-04-05

### Added
- **Graph Store Integration**: Integrated Neo4j to store documents and chunks as graph nodes with relational linkages (e.g., `HAS_CHUNK`).
- **External Vector Backend**: Added support for Qdrant as a remote vector storage option for scalable semantic search capabilities.
- **Tagging**: Established tagging support mapping documents and chunks for enriched metadata and better semantic queries.
- **Versioning**: Formally tagged release `0.0.4`.

## [0.0.3] - 2026-04-04

### Added
- **Hybrid Retrieval Orchestration**: Implemented `HybridRetrievalService` which fuses `PGVector` (semantic) and `PostgresFTS` (lexical) search paths using the Reciprocal Rank Fusion (RRF) algorithm.
- **Config-Driven Reranking**: Integrated a second-stage `CrossEncoderReranker` (`ms-marco-MiniLM-L-6-v2`) with a user-facing YAML and environment variable interface in `settings.yaml`.
- **Full-Text Search**: Added `PGFTSRetriever` utilizing Postgres `tsvector` and `GIN` indexing for robust keyword-based discovery.
- **RRF Fusion**: Developed a vectorized RRF implementation ($k=60$) to merge disparate rankings into a unified, high-relevance candidate list.

### Changed
- **Architectural Refactor**: Relocated the central configuration from `infrastructure/config.py` to `core/config.py` to reflect its role as a cross-cutting project concern.
- **Schema Modularization**: Decoupled `RetrievalFilter` and `ScoredChunk` from interface definitions into dedicated files in `domain/schemas/` to prevent circular dependencies.
- **Global Import Synchronization**: Updated 15+ files and the entire test suite to align with the new package structure and schema locations.
- **Persistence Evolution**: Enhanced the `ChunkDBModel` with automated `search_vector` management.


## [0.0.2] - 2026-04-03

### Added
- **Vector Intelligence**: Implemented `BaseEmbeddingEngine` and `HFEmbeddingEngine` using local `SentenceTransformers` (`all-MiniLM-L6-v2`) for cost-effective, high-performance semantic inference.
- **PGVector Persistence**: Integrated `pgvector` with SQLAlchemy; added 384-dimensional vector column to `ChunkDBModel` and implemented the `PGVectorStore` repository for durable vector management.
- **Semantic Retrieval**: Developed `VectorRetrievalService` to orchestrate query embedding and similarity-based retrieval, providing a foundation for natural language search.
- **Automated Schema Evolution**: Initialized `vector` extension and managed-column resizing via a robust Alembic migration cycle.
- **Integration Testing**: Established a dedicated e2e validation suite in `tests/integration/test_vector_retrieval.py` to ensure long-term pipeline stability.

### Changed
- **Ingestion Architecture**: Refactored the flat ingestion structure into a modular strategy-based layout with pluggable `chunkers` and `parsers`.
- **Document Parsing**: Replaced manual text extraction with a pluggable `ParserRegistry` supporting HTML (via `trafilatura`) and Markdown (via `markdown-it-py`).
- **Type Safety**: Achieved 100% strict Mypy compliance across 64 source files, including mandatory type-hinting of all test suites and library-specific stubs for `PyYAML`.
- **Quality Tooling**: Resolved 38 `ruff` linting violations, standardized logging to lazy formatting, and refactored `YamlConfigSettingsSource` for full alignment with `pydantic-settings` v2.
- **Persistence Simulation**: Updated the `InMemoryDocumentRepository` and associated test fixtures to correctly handle UUID serialization and strictly typed interfaces.

## [0.0.1] - 2026-04-02

### Added
- **Project Structure**: Flattened the repository layout (moved package to root) for better developer ergonomics.
- **Domain Models**: Established the foundational `Document` and `Chunk` entities.
- **Versioning**: Integrated `bump-my-version` for automated semantic versioning and git tagging.
- **Documentation**:
    - Added `CONTRIBUTING.md` with SemVer workflow and quality standards.
    - Initial `CHANGELOG.md` creation.
    - Updated `Architecture Overview` for the new internal organization.
- **Project Foundation**
    - Initialized CLEAN architecture with domain, application, and infrastructure layers.
    - Added comprehensive GSD planning infrastructure (PROJECT, REQUIREMENTS, ROADMAP).
    - `ruff` and `mypy` configurations updated for strict quality control.
    - `Alembic` persistence foundation initialized.
- **Improved Traceability**
    - Defined mandatory metadata schema for chunk-level traceability (doc_id, chunk_index, etc.).
- **Revised Roadmap**
    - Optimized milestone order: Embeddings first, Neo4j deferred to Phase 6.
