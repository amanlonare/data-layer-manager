from typing import Any

from mcp.server.fastmcp import FastMCP

from data_layer_manager.application.factories import get_search_service
from data_layer_manager.domain.schemas.strategy import (
    SearchStrategy,
    SearchStrategyConfig,
)


def register_search_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def search_knowledge(
        query: str,
        strategy: str = "hybrid",
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> str:
        """
        Search across the knowledge base using specific strategies.

        Strategies:
        - 'hybrid': Combines semantic vector similarity with keyword matching (Best balance).
        - 'vector': Pure semantic search (Great for concepts and synonyms).
        - 'keyword': Pure lexical matching (Best for exact IDs, technical terms, or rare names).
        - 'graph': Neo4j-based traversal (Best for seeing relationships between chunks).
        """
        # Map string strategy to Enum
        try:
            strategy_enum = SearchStrategy(strategy.lower())
        except ValueError:
            strategy_enum = SearchStrategy.HYBRID

        config = SearchStrategyConfig(name=strategy_enum)
        service = get_search_service(strategy_config=config)

        try:
            results = await service.search(query=query, limit=limit)

            if not results:
                return "No relevant knowledge found for the given query and strategy."

            formatted_results = []
            for i, res in enumerate(results, 1):
                source = res.chunk.metadata.get("source_locator", "unknown")
                formatted_results.append(
                    f"[{i}] Score: {res.score:.4f} | Source: {source}\n"
                    f"Content: {res.chunk.content}\n"
                )

            return "\n---\n".join(formatted_results)

        except Exception as e:
            return f"Error during search: {str(e)}"
