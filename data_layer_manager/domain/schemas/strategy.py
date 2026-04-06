from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class SearchStrategy(StrEnum):
    """
    Available retrieval strategies for the data layer.
    """

    HYBRID = "hybrid"  # Balanced: Vector (Semantic) + Postgres FTS (Lexical) using RRF.
    VECTOR = "vector"  # Semantic: Pure vector search (default backend).
    KEYWORD = "keyword"  # Lexical: Pure keyword search (default backend).
    GRAPH = "graph"  # Relational: Enhanced traversal via Neo4j connection nodes.

    # Explicit Backend Aliases (used by frontend)
    PGVECTOR = "pgvector"
    QDRANT = "qdrant"
    FTS = "fts"


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
