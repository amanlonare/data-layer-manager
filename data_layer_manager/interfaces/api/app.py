import asyncio
import logging
import shutil
import uuid
from pathlib import Path
from typing import Any

import neo4j
from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from neo4j import GraphDatabase
from qdrant_client import QdrantClient

from data_layer_manager.application.auth.security import get_api_key
from data_layer_manager.application.ingestion.chunkers.fixed_chunker import (
    FixedSizeChunker,
)
from data_layer_manager.application.ingestion.parser_registry import ParserRegistry
from data_layer_manager.application.ingestion.service import IngestionService
from data_layer_manager.application.retrieval.service import HybridRetrievalService
from data_layer_manager.core.config import get_settings
from data_layer_manager.domain.interfaces.embeddings import BaseEmbeddingEngine
from data_layer_manager.domain.interfaces.retrieval import BaseRetriever
from data_layer_manager.infrastructure.embeddings.hf_engine import HFEmbeddingEngine
from data_layer_manager.infrastructure.embeddings.openai_engine import (
    OpenAIEmbeddingEngine,
)
from data_layer_manager.infrastructure.graphstores.neo4j import Neo4jGraphStore
from data_layer_manager.infrastructure.parsers.html_parser import HTMLParser
from data_layer_manager.infrastructure.parsers.markdown_parser import MarkdownParser
from data_layer_manager.infrastructure.parsers.text_parser import TextParser
from data_layer_manager.infrastructure.persistence.database import SessionLocal
from data_layer_manager.infrastructure.persistence.repositories.document import (
    DocumentRepository,
)
from data_layer_manager.infrastructure.retrieval.fusion.rrf import RRFFusion
from data_layer_manager.infrastructure.retrieval.retrievers.neo4j_graph import (
    Neo4jRetriever,
)
from data_layer_manager.infrastructure.retrieval.retrievers.pgfts import (
    PostgresFTSRetriever,
)
from data_layer_manager.infrastructure.retrieval.retrievers.pgvector import (
    PGVectorRetriever,
)
from data_layer_manager.infrastructure.retrieval.retrievers.qdrant import (
    QdrantRetriever,
)
from data_layer_manager.infrastructure.vectorstores.qdrant.store import (
    QdrantVectorStore,
)
from data_layer_manager.interfaces.api.schemas import (
    IngestRequest,
    IngestResponse,
    SearchRequest,
    SearchResponse,
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Data Layer Manager API", version="0.0.5")

# Initialize global state dependencies
settings = get_settings()

# Initialize Soft Drivers (Limited Mode)
db_session = SessionLocal()
qdrant_client: QdrantClient | None = None
neo4j_driver: neo4j.Driver | None = None
embedding_engine: BaseEmbeddingEngine | None = None

try:
    qdrant_client = QdrantClient(
        url=settings.qdrant.url, timeout=settings.qdrant.timeout
    )
    # Check connection
    qdrant_client.get_collections()
    logger.info("Successfully connected to Qdrant.")
except Exception as e:
    logger.warning(f"Qdrant connection failed (Limited Mode active): {e}")

try:
    neo4j_driver = GraphDatabase.driver(
        settings.neo4j.url, auth=(settings.neo4j.username, settings.neo4j.password)
    )
    # Check connection
    if neo4j_driver:
        neo4j_driver.verify_connectivity()
        logger.info("Successfully connected to Neo4j.")
except Exception as e:
    logger.warning(f"Neo4j connection failed (Limited Mode active): {e}")

try:
    if settings.embeddings.provider == "openai":
        embedding_engine = OpenAIEmbeddingEngine(
            model_name=settings.embeddings.model_name,
            batch_size=settings.embeddings.batch_size,
        )
    else:
        embedding_engine = HFEmbeddingEngine(settings.embeddings)
    logger.info(f"Successfully loaded embedding engine: {settings.embeddings.provider}")
except Exception as e:
    logger.warning(f"Failed to load embedding engine: {e}")


def get_search_service(strategy: str | None = "hybrid") -> HybridRetrievalService:
    """Builds the retrieval pipeline based on the requested strategy."""
    retrievers: list[BaseRetriever] = []

    # 1. Dispatching based on strategy
    if strategy == "pgvector":
        if db_session and embedding_engine:
            retrievers.append(
                PGVectorRetriever(
                    session=db_session, embedding_service=embedding_engine
                )
            )

    elif strategy == "qdrant":
        if qdrant_client and embedding_engine:
            retrievers.append(
                QdrantRetriever(
                    client=qdrant_client,
                    embedding_service=embedding_engine,
                    settings=settings,
                )
            )

    elif strategy == "fts":
        if db_session:
            retrievers.append(PostgresFTSRetriever(session=db_session))

    elif strategy == "graph":
        if neo4j_driver:
            retrievers.append(Neo4jRetriever(driver=neo4j_driver))

    else:  # Default: hybrid
        if qdrant_client and embedding_engine:
            retrievers.append(
                QdrantRetriever(
                    client=qdrant_client,
                    embedding_service=embedding_engine,
                    settings=settings,
                )
            )
        if db_session:
            retrievers.append(PostgresFTSRetriever(session=db_session))
        if neo4j_driver:
            retrievers.append(Neo4jRetriever(driver=neo4j_driver))

    return HybridRetrievalService(retrievers=retrievers, fusion_strategy=RRFFusion())


def get_ingestion_service() -> IngestionService:
    """Builds the ingestion pipeline with Registry + Chunker + Repos"""
    registry = ParserRegistry()
    registry.register(".html", HTMLParser())
    registry.register(".md", MarkdownParser())
    registry.register(".txt", TextParser())
    registry.set_fallback(TextParser())

    chunker = FixedSizeChunker()

    # Qdrant vector store (optional — only if client is connected)
    vector_store = None
    if qdrant_client:
        try:
            vector_store = QdrantVectorStore(client=qdrant_client)
        except Exception as e:
            logger.warning(
                f"QdrantVectorStore init failed during ingestion wiring: {e}"
            )

    doc_repo = None
    if db_session:
        doc_repo = DocumentRepository(session=db_session)

    # Neo4j graph store (optional — only if driver is connected)
    graph_store = None
    if neo4j_driver:
        try:
            graph_store = Neo4jGraphStore(driver=neo4j_driver)
        except Exception as e:
            logger.warning(f"Neo4jGraphStore init failed during ingestion wiring: {e}")

    return IngestionService(
        parser_registry=registry,
        chunker=chunker,
        document_repository=doc_repo,
        embedding_engine=embedding_engine,
        vector_store=vector_store,
        graph_store=graph_store,
    )


search_service = get_search_service()
ingestion_service = get_ingestion_service()

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
    # Use the strategy from the request to build the service
    service = get_search_service(strategy=request.strategy)

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
async def ingest_text(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
    service: IngestionService = Depends(get_ingestion_service),
    api_key: str = Depends(get_api_key),
) -> IngestResponse:
    """
    Ingest raw text content directly via JSON.
    """
    task_id = str(uuid.uuid4())
    tasks_status[task_id] = {"status": "queued", "progress": 0}

    # Ensure temporary directory exists
    temp_dir = Path(".tmp/text_ingest")
    temp_dir.mkdir(parents=True, exist_ok=True)

    temp_path = temp_dir / f"{task_id}.txt"
    with temp_path.open("w", encoding="utf-8") as f:
        f.write(request.content)

    background_tasks.add_task(background_ingest_real, task_id, str(temp_path), service)

    return IngestResponse(
        task_id=task_id,
        status="accepted",
        message=f"Text content accepted for processing. Tracking ID: {task_id}",
    )


@app.get("/v1/tasks/{task_id}", tags=["ingestion"])
async def get_task_status(task_id: str) -> dict[str, Any]:
    """Check the status of an ingestion task."""
    if task_id not in tasks_status:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks_status[task_id]


async def background_ingest(task_id: str, request: IngestRequest) -> None:
    """Simulated background ingestion with progress updates."""
    tasks_status[task_id] = {"status": "processing", "progress": 0}

    # Simulate steps
    steps = ["parsing", "chunking", "embedding", "indexing"]
    for i, step in enumerate(steps):
        await asyncio.sleep(1)  # Simulate work
        tasks_status[task_id] = {
            "status": "processing",
            "progress": int((i + 1) / len(steps) * 100),
            "current_step": step,
        }

    tasks_status[task_id] = {"status": "completed", "progress": 100}


@app.post(
    "/v1/ingest/upload",
    response_model=IngestResponse,
    tags=["ingestion"],
)
async def ingest_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    service: IngestionService = Depends(get_ingestion_service),
    api_key: str = Depends(get_api_key),
) -> IngestResponse:
    """
    Real-world file upload endpoint.
    """
    task_id = str(uuid.uuid4())
    tasks_status[task_id] = {"status": "queued", "progress": 0}

    # Ensure temporary upload directory exists
    upload_dir = Path(".tmp/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    temp_path = upload_dir / f"{task_id}_{file.filename}"

    # Write file stream to local disk for processing
    with temp_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(background_ingest_real, task_id, str(temp_path), service)

    return IngestResponse(
        task_id=task_id,
        status="accepted",
        message=f"File '{file.filename}' accepted for processing. Tracking ID: {task_id}",
    )


async def background_ingest_real(
    task_id: str, file_path: str, service: IngestionService
) -> None:
    """Orchestrates actual parsing, chunking, and indexing logic."""
    tasks_status[task_id] = {"status": "processing", "progress": 10}
    path = Path(file_path)

    try:
        tasks_status[task_id].update({"status": "parsing", "progress": 25})

        # If no real service is wired (simulation mode), we still follow the logic
        if not service.document_repository:
            logger.warning(
                "No document repository connected. Falling back to simulation."
            )
            await asyncio.sleep(1)  # Simulated Parsing
            tasks_status[task_id].update({"status": "chunking", "progress": 50})
            await asyncio.sleep(1)  # Simulated Chunking
            tasks_status[task_id].update({"status": "indexing", "progress": 80})
            await asyncio.sleep(1)  # Simulated Vectorization
        else:
            # Execute real pipeline
            logger.info(f"Starting real ingestion for {file_path}")
            # Use metadata dictionary as expected by ingest_file
            doc_metadata = {
                "source_type": "upload",
                "file_type": path.suffix[1:] if path.suffix else "txt",
            }
            # We run this in a threadpool to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, service.ingest_file, file_path, doc_metadata
            )

        tasks_status[task_id] = {"status": "completed", "progress": 100}
    except Exception as e:
        logger.error(f"Ingestion failed for task {task_id}: {e}")
        tasks_status[task_id] = {"status": "failed", "progress": 0, "error": str(e)}
    finally:
        # Cleanup temporary file
        if path.exists():
            path.unlink()
