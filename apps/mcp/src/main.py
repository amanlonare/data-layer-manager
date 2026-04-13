import logging
import sys

from mcp.server.fastmcp import FastMCP

from apps.mcp.src.tools.ingest import register_ingest_tools
from apps.mcp.src.tools.search import register_search_tools

# Configure logging to stderr (FastMCP uses stdout for JSON-RPC)
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastMCP Server
mcp = FastMCP("Data Layer Manager")

# Register Tools
register_search_tools(mcp)
register_ingest_tools(mcp)

if __name__ == "__main__":
    # Start the server via stdio (Default transport)
    logger.info("Starting Data Layer Manager MCP server via stdio...")
    mcp.run()
