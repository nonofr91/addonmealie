import logging
import traceback
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from mealie import MealieFetcher

logger = logging.getLogger("mealie-mcp")


def register_ingredients_tools(mcp: FastMCP, mealie: MealieFetcher) -> None:
    """Register all ingredient-related tools (foods and units) with the MCP server."""

    @mcp.tool()
    def get_foods_list(
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get all foods with optional filtering.

        Args:
            page: Page number to retrieve
            per_page: Number of items per page
            search: Search term to filter foods

        Returns:
            Dict[str, Any]: Food items with pagination information
        """
        try:
            logger.info({"message": "Fetching foods", "page": page, "per_page": per_page, "search": search})
            return mealie.get_foods(page=page, per_page=per_page, search=search)
        except Exception as e:
            error_msg = f"Error fetching foods: {str(e)}"
            logger.error({"message": error_msg})
            logger.debug({"message": "Error traceback", "traceback": traceback.format_exc()})
            raise ToolError(error_msg)

    @mcp.tool()
    def search_foods_by_name(
        name: str,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Search foods by name.

        Args:
            name: Food name to search for
            page: Page number to retrieve
            per_page: Number of items per page

        Returns:
            Dict[str, Any]: Matching foods with pagination information
        """
        try:
            logger.info({"message": "Searching foods", "name": name})
            return mealie.search_foods_by_name(name=name, page=page, per_page=per_page)
        except Exception as e:
            error_msg = f"Error searching foods: {str(e)}"
            logger.error({"message": error_msg})
            logger.debug({"message": "Error traceback", "traceback": traceback.format_exc()})
            raise ToolError(error_msg)

    @mcp.tool()
    def get_food(food_id: str) -> Dict[str, Any]:
        """Get a specific food by ID.

        Args:
            food_id: The UUID of the food

        Returns:
            Dict[str, Any]: Food details
        """
        try:
            logger.info({"message": "Fetching food", "food_id": food_id})
            return mealie.get_food(food_id)
        except Exception as e:
            error_msg = f"Error fetching food with ID '{food_id}': {str(e)}"
            logger.error({"message": error_msg})
            logger.debug({"message": "Error traceback", "traceback": traceback.format_exc()})
            raise ToolError(error_msg)

    @mcp.tool()
    def create_food_ingredient(
        name: str,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new food ingredient.

        Args:
            name: Name of the food
            description: Optional description

        Returns:
            Dict[str, Any]: The created food details
        """
        try:
            logger.info({"message": "Creating food", "name": name})
            return mealie.create_food(name=name, description=description)
        except Exception as e:
            error_msg = f"Error creating food '{name}': {str(e)}"
            logger.error({"message": error_msg})
            logger.debug({"message": "Error traceback", "traceback": traceback.format_exc()})
            raise ToolError(error_msg)

    @mcp.tool()
    def get_units_list(
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get all measurement units with optional filtering.

        Args:
            page: Page number to retrieve
            per_page: Number of items per page
            search: Search term to filter units

        Returns:
            Dict[str, Any]: Unit items with pagination information
        """
        try:
            logger.info({"message": "Fetching units", "page": page, "per_page": per_page, "search": search})
            return mealie.get_units(page=page, per_page=per_page, search=search)
        except Exception as e:
            error_msg = f"Error fetching units: {str(e)}"
            logger.error({"message": error_msg})
            logger.debug({"message": "Error traceback", "traceback": traceback.format_exc()})
            raise ToolError(error_msg)

    @mcp.tool()
    def get_unit(unit_id: str) -> Dict[str, Any]:
        """Get a specific unit by ID.

        Args:
            unit_id: The UUID of the unit

        Returns:
            Dict[str, Any]: Unit details
        """
        try:
            logger.info({"message": "Fetching unit", "unit_id": unit_id})
            return mealie.get_unit(unit_id)
        except Exception as e:
            error_msg = f"Error fetching unit with ID '{unit_id}': {str(e)}"
            logger.error({"message": error_msg})
            logger.debug({"message": "Error traceback", "traceback": traceback.format_exc()})
            raise ToolError(error_msg)

    @mcp.tool()
    def create_measurement_unit(
        name: str,
        description: Optional[str] = None,
        abbreviation: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new measurement unit.

        Args:
            name: Name of the unit
            description: Optional description
            abbreviation: Optional abbreviation

        Returns:
            Dict[str, Any]: The created unit details
        """
        try:
            logger.info({"message": "Creating unit", "name": name})
            return mealie.create_unit(name=name, description=description, abbreviation=abbreviation)
        except Exception as e:
            error_msg = f"Error creating unit '{name}': {str(e)}"
            logger.error({"message": error_msg})
            logger.debug({"message": "Error traceback", "traceback": traceback.format_exc()})
            raise ToolError(error_msg)
