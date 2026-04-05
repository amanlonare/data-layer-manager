from typing import Any

from mcp.server.fastmcp import FastMCP

from data_layer_manager.interfaces.api.schemas import IngestRequest, SearchRequest

# Create an MCP server with FastMCP
mcp = FastMCP("Data Layer Manager")


@mcp.tool()
async def search_knowledge(
    query: str,
    limit: int = 10,
    filters: dict[str, Any] | None = None,
    strategy: str | None = None,
) -> str:
    """
    Search the hybrid data layer (Vector + Graph) for relevant information.

    Args:
        query: The search query.
        limit: Number of results to return.
        filters: Metadata filters to apply (e.g. {"source_type": "file"}).
        strategy: Retrieval strategy (e.g., 'hybrid', 'vector', 'keyword').
    """
    # Explicitly pass filters to resolve the 'Missing named argument' error
    _ = SearchRequest(query=query, limit=limit, filters=filters, strategy=strategy)

    # Wiring pending Docker Compose setup
    # In next phase, this will use the injected HybridRetrievalService
    raise NotImplementedError(
        "HybridRetrievalService wiring is pending backend services. "
        "Run `make services-up && make db-init` first."
    )


@mcp.tool()
async def ingest_knowledge(
    content: str, source: str | None = None, metadata: dict[str, Any] | None = None
) -> str:
    """
    Ingest new text content into the data layer.

    Args:
        content: The text content to ingest.
        source: Optional source identifier.
        metadata: Optional metadata for categorization.
    """
    # Contract alignment: Map to IngestRequest model
    _ = IngestRequest(content=content, source=source, metadata=metadata)

    # Wiring pending Docker Compose setup
    raise NotImplementedError(
        "IngestionService wiring is pending backend services. "
        "Run `make services-up && make db-init` first."
    )


if __name__ == "__main__":
    # Standard MCP stdio entry point
    mcp.run(transport="stdio")
