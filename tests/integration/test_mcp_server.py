import pytest

from apps.mcp.src.main import mcp
from data_layer_manager.application.factories import (
    get_ingestion_service,
    get_search_service,
)


@pytest.mark.asyncio
async def test_mcp_server_initialization() -> None:
    """Verify that the MCP server object is correctly initialized and has the expected tools."""
    assert mcp.name == "Data Layer Manager"

    # Check that search and ingest tools are registered
    tool_names = [tool.name for tool in await mcp.list_tools()]
    assert "search_knowledge" in tool_names
    assert "ingest_knowledge" in tool_names


def test_shared_factories_initialization() -> None:
    """Verify that backend services can be instantiated through shared factories."""
    search_service = get_search_service()
    assert search_service is not None

    ingestion_service = get_ingestion_service()
    assert ingestion_service is not None


@pytest.mark.asyncio
async def test_search_tool_execution_smoke() -> None:
    """Smoke test: execute search tool with a simple query."""
    # Call the tool through the FastMCP instance
    result = await mcp.call_tool("search_knowledge", arguments={"query": "test query"})

    # Verify we got some content back
    assert result is not None
    # result is typically a list of Content objects
    # We'll check the string representation for our formatted output markers
    result_str = str(result)
    assert "Score:" in result_str or "No relevant knowledge found" in result_str
