# Celery Task Boundary & Worker Design

`data-layer-manager` uses Celery for all long-running, resource-intensive, or external-dependent operations. This ensures that the REST API remains responsive and low-latency.

## Core Principles

1.  **Atomicity**: Tasks should perform a single logical unit of work.
2.  **Idempotency**: All ingestion and maintenance tasks must be safe to retry without creating duplicate data or corrupted states.
3.  **Visibility**: Every background job is tracked in the persistence layer via an `IngestionJob` record.
4.  **Queue Separation**: Workloads are isolated by queue to manage resources and concurrency effectively.

## Queue Strategy

We use three primary queues:

| Queue | Workload Characteristics | Example Tasks |
| :--- | :--- | :--- |
| **`ingestion`** | High CPU/IO, long-running | Parsing files, generating embeddings, vector storage. |
| **`maintenance`** | Low CPU, scheduled | Reindexing, cleanup of failed jobs, cache invalidation. |
| **`default`**| General-purpose | Webhooks, telemetry sync, small notifications. |

## Task Definitions

### Ingestion Pipeline Tasks
-   **`process_ingestion_job(job_id)`**: The high-level orchestrator.
-   **`parse_and_clean_document(doc_id)`**: Extracts text from raw bytes (PDF/DOCX) and applies cleaning rules.
-   **`chunk_and_embed_document(doc_id)`**: Splits text into segments and calls the embedding provider.
-   **`index_document_chunks(doc_id)`**: Upserts embeddings into pgvector or Qdrant.

### Maintenance Tasks
-   **`reindex_all_documents()`**: Full sweep for version upgrades or model changes.
-   **`cleanup_orphaned_chunks()`**: Removing chunks where parents no longer exist.

## Error Handling & Resiliency

-   **Retries**: Tasks interfacing with external providers (OpenAI, Qdrant) use exponential backoff.
-   **Visibility Time**: Set to 1 hour for large batch ingestion to avoid multiple workers picking up the same job.
-   **Dead Letter Queue (DLQ)**: Failed tasks after max retries are moved to a `failed_tasks` queue for manual inspection.

## Observability

-   **Standardized Logs**: Every task logs its `job_id` and `request_id` for cross-system traceability.
-   **State Sync**: Tasks update the `IngestionJob.status` (e.g., `PARSING`, `EMBEDDING`, `COMPLETED`, `FAILED`) at each boundary.
