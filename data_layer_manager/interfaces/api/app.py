import logging
import shutil
import uuid
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from data_layer_manager.application.auth.security import get_api_key
from data_layer_manager.application.factories import (
    get_ingestion_service,
    get_search_service,
)
from data_layer_manager.interfaces.api.schemas import (
    IngestRequest,
    IngestResponse,
    SearchRequest,
    SearchResponse,
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Data Layer Manager API", version="0.0.5")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory task tracking (Simple for now, could move to Redis/DB)
tasks_status: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------


@app.get("/health", tags=["ops"])
async def health_check() -> dict[str, str]:
    """Health check endpoint for deployment and service verification."""
    return {"status": "ok", "version": "0.0.5"}


# ---------------------------------------------------------------------------
# Protected endpoints
# ---------------------------------------------------------------------------


@app.post(
    "/v1/search",
    response_model=SearchResponse,
    tags=["retrieval"],
)
async def search(
    request: SearchRequest, api_key: str = Depends(get_api_key)
) -> SearchResponse:
    """
    Unified Hybrid + Graph retrieval endpoint.
    """
    # Use the structured strategy config from the request
    service = get_search_service(strategy_config=request.strategy)

    try:
        results = await service.search(query=request.query, limit=request.limit)
        # Convert domain ScoredChunk entities to API SearchResult dicts
        api_results = [
            {
                "id": str(res.chunk.id),
                "content": res.chunk.content,
                "score": res.score,
                "metadata": {
                    "source": res.chunk.metadata.get("source_locator", "unknown"),
                    "file_type": res.chunk.metadata.get("file_type", "unknown"),
                },
            }
            for res in results
        ]
        return SearchResponse(
            results=api_results,
            metadata={"query": request.query, "total": len(api_results)},
        )
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/v1/ingest",
    response_model=IngestResponse,
    tags=["ingestion"],
)
async def ingest(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(get_api_key),
) -> IngestResponse:
    service = get_ingestion_service()
    task_id = str(uuid.uuid4())
    tasks_status[task_id] = {"status": "processing", "message": "Starting ingestion"}

    async def run_ingestion() -> None:
        try:
            doc_id, count = await service.ingest_text(
                content=request.content,
                source_locator=request.source or "api_upload",
                metadata=request.metadata or {},
            )
            tasks_status[task_id] = {
                "status": "completed",
                "document_id": str(doc_id),
                "chunk_count": count,
            }
        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            tasks_status[task_id] = {"status": "failed", "message": str(e)}

    background_tasks.add_task(run_ingestion)
    return IngestResponse(task_id=task_id)


@app.post(
    "/v1/ingest/file",
    response_model=IngestResponse,
    tags=["ingestion"],
)
async def ingest_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    api_key: str = Depends(get_api_key),
) -> IngestResponse:
    service = get_ingestion_service()
    task_id = str(uuid.uuid4())
    tasks_status[task_id] = {"status": "processing", "message": "Saving file"}

    # Save file to temp location
    temp_dir = Path("/tmp/data-layer-manager")
    temp_dir.mkdir(parents=True, exist_ok=True)
    file_path = temp_dir / f"{task_id}_{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    async def run_ingestion() -> None:
        try:
            document = await service.ingest_file(
                file_path=str(file_path),
                source_metadata={"file_name": file.filename},
            )
            tasks_status[task_id] = {
                "status": "completed",
                "document_id": str(document.id),
                "chunk_count": len(document.chunks),
            }
        except Exception as e:
            logger.error(f"File ingestion failed: {e}")
            tasks_status[task_id] = {"status": "failed", "message": str(e)}
        finally:
            if file_path.exists():
                file_path.unlink()

    background_tasks.add_task(run_ingestion)
    return IngestResponse(task_id=task_id)


@app.get("/v1/tasks/{task_id}", tags=["ops"])
async def get_task_status(task_id: str) -> dict[str, Any]:
    if task_id not in tasks_status:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks_status[task_id]
