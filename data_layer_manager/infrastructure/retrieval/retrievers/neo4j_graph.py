import logging
from uuid import UUID

from neo4j import Driver

from data_layer_manager.domain.entities.chunk import Chunk
from data_layer_manager.domain.interfaces.retrieval import BaseRetriever
from data_layer_manager.domain.schemas.retrieval_filter import RetrievalFilter
from data_layer_manager.domain.schemas.scored_chunk import ScoredChunk

logger = logging.getLogger(__name__)


class Neo4jRetriever(BaseRetriever):
    """
    Relational search strategy using Neo4j.
    Finds chunks based on keyword matches and expands to related entities.
    """

    def __init__(self, driver: Driver):
        self._driver = driver

    @property
    def id(self) -> str:
        return "neo4j_relational"

    async def retrieve(
        self, query: str, filter_: RetrievalFilter, limit: int = 30
    ) -> list[ScoredChunk]:
        """
        Retrieves chunks using Cypher keyword matching and relationship traversal.
        """
        # Split query into keywords for a simple CONTAINS search
        # In a production system, we would use Neo4j Full-Text Search indexes.
        keywords = [k for k in query.split() if len(k) > 2]
        if not keywords:
            return []

        # Build a Cypher query that matches any keyword in the content
        # and expands to find neighboring chunks and the parent document.
        cypher_query = """
        MATCH (c:Chunk)
        WHERE any(k IN $keywords WHERE c.content CONTAINS k)

        // Relational Expansion: Find chunks in the same document or linked entities
        OPTIONAL MATCH (c)<-[:HAS_CHUNK]-(d:Document)-[:HAS_CHUNK]->(peer:Chunk)

        WITH c, d, count(peer) as peer_count,
             [k IN $keywords WHERE c.content CONTAINS k] as matches

        RETURN c.id as id,
               c.content as content,
               c.chunk_strategy as chunk_strategy,
               c.file_type as file_type,
               d.id as document_id,
               d.source_type as source_type,
               d.source_category as source_category,
               size(matches) as match_score
        ORDER BY match_score DESC
        LIMIT $limit
        """

        parameters = {"keywords": keywords, "limit": limit}

        scored_chunks = []

        # NOTE: Using synchronous driver inside async retrieve for now.
        # In heavy production, use Neo4j's AsyncDriver.
        with self._driver.session() as session:
            result = session.run(cypher_query, parameters)
            for record in result:
                try:
                    chunk = Chunk(
                        id=UUID(record["id"]),
                        document_id=UUID(record["document_id"]),
                        content=record["content"],
                        chunk_strategy=record["chunk_strategy"],
                        source_type=record["source_type"],
                        source_category=record["source_category"],
                        file_type=record["file_type"],
                        status="COMPLETED",
                        metadata={"match_score": record["match_score"]},
                    )

                    # Normalize score to 0..1 range (simple heuristic)
                    score = min(1.0, record["match_score"] / len(keywords))

                    scored_chunks.append(
                        ScoredChunk(chunk=chunk, score=score, retriever_id=self.id)
                    )
                except Exception as e:
                    logger.warning(f"Failed to parse Neo4j record: {e}")
                    continue

        return scored_chunks
