from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class SearchStrategy(StrEnum):
    """
    Available retrieval strategies for the data layer.
    """

    HYBRID = "hybrid"  # Balanced: Vector (Semantic) + Postgres FTS (Lexical) using RRF.
    VECTOR = "vector"  # Semantic: Pure vector search using pgvector or Qdrant.
    KEYWORD = "keyword"  # Lexical: Pure full-text search using Postgres FTS.
    GRAPH = "graph"  # Relational: Enhanced traversal via Neo4j connection nodes.


class SearchStrategyConfig(BaseModel):
    """
    Structured configuration for the retrieval strategy.

    Allows for providing optional parameters to tune the specific strategy performance.
    """

    name: SearchStrategy = Field(
        default=SearchStrategy.HYBRID,
        description=(
            "The core strategy to use: "
            "'hybrid' is the most robust (Vector + Keyword fusion), "
            "'vector' for semantic similarity, "
            "'keyword' for exact term matching, "
            "'graph' for relationship-aware retrieval."
        ),
    )
    parameters: dict[str, Any] | None = Field(
        default=None,
        description="Optional strategy-specific tuning parameters (e.g., {'alpha': 0.5}).",
    )
