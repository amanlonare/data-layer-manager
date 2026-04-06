from typing import Any

from mcp.server.fastmcp import FastMCP

from data_layer_manager.application.factories import get_ingestion_service


def register_ingest_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def ingest_knowledge(
        content: str,
        source: str = "mcp_tool",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Indexes raw text into the knowledge base for future retrieval.

        Args:
            content: The text content to ingest.
            source: A human-readable identifier for the source (e.g., 'slack_thread').
            metadata: Optional key-value pairs to store with the document.
        """
        service = get_ingestion_service()

        try:
            doc_id, chunk_count = await service.ingest_text(
                content=content,
                source_locator=source,
                metadata=metadata or {},
            )

            return (
                f"Successfully ingested knowledge.\n"
                f"Document ID: {doc_id}\n"
                f"Chunks indexed: {chunk_count}"
            )

        except Exception as e:
            return f"Error during ingestion: {str(e)}"
