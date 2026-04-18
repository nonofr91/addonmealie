import logging
import os
import sys
import traceback
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from mealie import MealieFetcher
from prompts import register_prompts
from tools import register_all_tools

# Load environment variables from .env file only if not already set in environment
# This allows Windsurf MCP config env vars to take precedence
load_dotenv(override=False)

# Get log level from environment variable with INFO as default
log_level_name = os.getenv("LOG_LEVEL", "INFO")
log_level = getattr(logging, log_level_name.upper(), logging.INFO)

# Configure logging
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("mealie_mcp_server.log")],
)
logger = logging.getLogger("mealie-mcp")

mcp = FastMCP("mealie")

MEALIE_BASE_URL = os.getenv("MEALIE_BASE_URL")
MEALIE_API_KEY = os.getenv("MEALIE_API_KEY")

# Allow server to start without credentials, but warn if missing
if not MEALIE_BASE_URL or not MEALIE_API_KEY:
    logger.warning(
        "MEALIE_BASE_URL or MEALIE_API_KEY not set. Server will start but API calls will fail."
    )
    mealie = None
else:
    try:
        mealie = MealieFetcher(
            base_url=MEALIE_BASE_URL,
            api_key=MEALIE_API_KEY,
        )
    except Exception as e:
        logger.error({"message": "Failed to initialize Mealie client", "error": str(e)})
        logger.debug({"message": "Error traceback", "traceback": traceback.format_exc()})
        mealie = None

register_prompts(mcp)
register_all_tools(mcp, mealie)


def main():
    """Main entry point for the MCP server."""
    try:
        # Get transport from environment variable with stdio as default for local development
        mcp_transport = os.getenv("MCP_TRANSPORT", "stdio")
        logger.info({"message": "Starting Mealie MCP Server", "transport": mcp_transport})

        # For SSE transport, we need to specify host and port
        if mcp_transport == "sse":
            mcp.run(transport="sse", host="0.0.0.0", port=int(os.getenv("MCP_PORT", "8000")), dns_rebinding_protection=True)
        else:
            mcp.run(transport=mcp_transport, dns_rebinding_protection=True)
    except Exception as e:
        logger.critical(
            {"message": "Fatal error in Mealie MCP Server", "error": str(e)}
        )
        logger.debug(
            {"message": "Error traceback", "traceback": traceback.format_exc()}
        )
        raise


if __name__ == "__main__":
    main()
