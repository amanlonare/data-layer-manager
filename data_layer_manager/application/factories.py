import logging

from neo4j import Driver, GraphDatabase
from qdrant_client import QdrantClient
from sqlalchemy.orm import Session

from data_layer_manager.application.ingestion.chunkers.fixed_chunker import (
    FixedSizeChunker,
)
from data_layer_manager.application.ingestion.parser_registry import ParserRegistry
from data_layer_manager.application.ingestion.service import IngestionService
from data_layer_manager.application.retrieval.service import HybridRetrievalService
from data_layer_manager.core.config import Settings, get_settings
from data_layer_manager.domain.interfaces.embeddings import BaseEmbeddingEngine
from data_layer_manager.domain.interfaces.retrieval import BaseRetriever
from data_layer_manager.domain.schemas.strategy import (
    SearchStrategy,
    SearchStrategyConfig,
)
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

logger = logging.getLogger(__name__)

# Global singleton-like state for drivers (Lazy loaded)
_settings: Settings | None = None
_db_session: Session | None = None
_qdrant_client: QdrantClient | None = None
_neo4j_driver: Driver | None = None
_embedding_engine: BaseEmbeddingEngine | None = None


def _get_drivers() -> tuple[
    Settings,
    Session | None,
    QdrantClient | None,
    Driver | None,
    BaseEmbeddingEngine | None,
]:
    """Initializes and returns shared drivers."""
    global _settings, _db_session, _qdrant_client, _neo4j_driver, _embedding_engine

    if _settings is None:
        _settings = get_settings()

    if _db_session is None:
        _db_session = SessionLocal()

    if _qdrant_client is None:
        try:
            _qdrant_client = QdrantClient(
                url=_settings.qdrant.url, timeout=_settings.qdrant.timeout
            )
            # Connectivity check
            _qdrant_client.get_collections()
        except Exception as e:
            logger.warning(f"Qdrant connection failed: {e}")
            _qdrant_client = None

    if _neo4j_driver is None:
        try:
            _neo4j_driver = GraphDatabase.driver(
                _settings.neo4j.url,
                auth=(_settings.neo4j.username, _settings.neo4j.password),
            )
            _neo4j_driver.verify_connectivity()
        except Exception as e:
            logger.warning(f"Neo4j connection failed: {e}")
            _neo4j_driver = None

    if _embedding_engine is None:
        try:
            if _settings.embeddings.provider == "openai":
                _embedding_engine = OpenAIEmbeddingEngine(
                    model_name=_settings.embeddings.model_name,
                    batch_size=_settings.embeddings.batch_size,
                )
            else:
                _embedding_engine = HFEmbeddingEngine(_settings.embeddings)
        except Exception as e:
            logger.warning(f"Failed to load embedding engine: {e}")
            _embedding_engine = None

    return _settings, _db_session, _qdrant_client, _neo4j_driver, _embedding_engine


def get_search_service(
    strategy_config: SearchStrategyConfig | None = None,
) -> HybridRetrievalService:
    """Builds the retrieval pipeline based on the requested strategy."""
    settings, db_session, qdrant_client, neo4j_driver, embedding_engine = _get_drivers()

    strategy_config = strategy_config or SearchStrategyConfig()
    name = strategy_config.name
    retrievers: list[BaseRetriever] = []

    if name == SearchStrategy.VECTOR:
        if qdrant_client and embedding_engine:
            retrievers.append(
                QdrantRetriever(
                    client=qdrant_client,
                    embedding_service=embedding_engine,
                    settings=settings,
                )
            )
        elif db_session and embedding_engine:
            retrievers.append(
                PGVectorRetriever(
                    session=db_session, embedding_service=embedding_engine
                )
            )

    elif name == SearchStrategy.QDRANT:
        if qdrant_client and embedding_engine:
            retrievers.append(
                QdrantRetriever(
                    client=qdrant_client,
                    embedding_service=embedding_engine,
                    settings=settings,
                )
            )

    elif name == SearchStrategy.PGVECTOR:
        if db_session and embedding_engine:
            retrievers.append(
                PGVectorRetriever(
                    session=db_session, embedding_service=embedding_engine
                )
            )

    elif name in [SearchStrategy.KEYWORD, SearchStrategy.FTS]:
        if db_session:
            retrievers.append(PostgresFTSRetriever(session=db_session))

    elif name == SearchStrategy.GRAPH:
        if neo4j_driver:
            retrievers.append(Neo4jRetriever(driver=neo4j_driver))

    elif name == SearchStrategy.HYBRID:
        if qdrant_client and embedding_engine:
            retrievers.append(
                QdrantRetriever(
                    client=qdrant_client,
                    embedding_service=embedding_engine,
                    settings=settings,
                )
            )
        elif db_session and embedding_engine:
            retrievers.append(
                PGVectorRetriever(
                    session=db_session, embedding_service=embedding_engine
                )
            )
        if db_session:
            retrievers.append(PostgresFTSRetriever(session=db_session))

    else:
        # Default or fallback
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

    return HybridRetrievalService(retrievers=retrievers, fusion_strategy=RRFFusion())


def get_ingestion_service() -> IngestionService:
    """Builds the ingestion pipeline with Registry + Chunker + Repos"""
    settings, db_session, qdrant_client, neo4j_driver, embedding_engine = _get_drivers()

    registry = ParserRegistry()
    registry.register(".html", HTMLParser())
    registry.register(".md", MarkdownParser())
    registry.register(".txt", TextParser())
    registry.set_fallback(TextParser())

    chunker = FixedSizeChunker()

    vector_store = None
    if qdrant_client:
        try:
            vector_store = QdrantVectorStore(client=qdrant_client)
        except Exception:
            pass

    doc_repo = None
    if db_session:
        doc_repo = DocumentRepository(session=db_session)

    graph_store = None
    if neo4j_driver:
        try:
            graph_store = Neo4jGraphStore(driver=neo4j_driver)
        except Exception:
            pass

    return IngestionService(
        parser_registry=registry,
        chunker=chunker,
        document_repository=doc_repo,
        embedding_engine=embedding_engine,
        vector_store=vector_store,
        graph_store=graph_store,
    )
