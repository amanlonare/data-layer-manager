# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.2] - 2026-04-03

### Changed
- **Ingestion Architecture**: Refactored the flat ingestion structure into a modular strategy-based layout with a dedicated `chunkers` directory.
- **Document Parsing**: Replaced manual text extraction with a pluggable `ParserRegistry` supporting HTML (via `trafilatura`) and Markdown (via `markdown-it-py`).
- **Type Safety**: Hardened the codebase against runtime failures by resolving 15 Mypy type-check errors in the core domain and infrastructure.
- **Persistence Simulation**: Updated the `InMemoryDocumentRepository` and associated test fixtures to correctly handle UUID serialization and strictly typed interfaces.
- **Quality Tooling**: Standardized logging to lazy formatting and resolved multiple `ruff` linting regressions identified during the refactor.

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
