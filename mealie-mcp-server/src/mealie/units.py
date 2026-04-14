import logging
from typing import Any, Dict, List, Optional

from utils import format_api_params

logger = logging.getLogger("mealie-mcp")


class UnitsMixin:
    """Mixin class for measurement unit-related API endpoints"""

    def get_units(
        self,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        order_by: Optional[str] = None,
        order_direction: Optional[str] = None,
        search: Optional[str] = None,
        query_filter: Optional[str] = None,
        order_by_null_position: Optional[str] = None,
        pagination_seed: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get all measurement units.

        Args:
            page: Page number to retrieve
            per_page: Number of items per page
            order_by: Field to order results by
            order_direction: Direction to order results ('asc' or 'desc')
            search: Search term to filter units
            query_filter: Advanced query filter
            order_by_null_position: How to handle nulls in ordering ('first' or 'last')
            pagination_seed: Seed for consistent pagination

        Returns:
            JSON response containing unit items and pagination information
        """
        param_dict = {
            "page": page,
            "perPage": per_page,
            "orderBy": order_by,
            "orderDirection": order_direction,
            "search": search,
            "queryFilter": query_filter,
            "orderByNullPosition": order_by_null_position,
            "paginationSeed": pagination_seed,
        }

        params = format_api_params(param_dict)

        logger.info({"message": "Retrieving units", "parameters": params})
        return self._handle_request("GET", "/api/units", params=params)

    def get_unit(self, unit_id: str) -> Dict[str, Any]:
        """Get a specific unit by ID.

        Args:
            unit_id: The UUID of the unit

        Returns:
            JSON response containing the unit details
        """
        if not unit_id:
            raise ValueError("Unit ID cannot be empty")

        logger.info({"message": "Retrieving unit", "unit_id": unit_id})
        return self._handle_request("GET", f"/api/units/{unit_id}")

    def create_unit(
        self,
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
            JSON response containing the created unit
        """
        if not name:
            raise ValueError("Unit name cannot be empty")

        payload = {"name": name}
        if description:
            payload["description"] = description
        if abbreviation:
            payload["abbreviation"] = abbreviation

        logger.info({"message": "Creating unit", "name": name})
        return self._handle_request("POST", "/api/units", json=payload)

    def update_unit(self, unit_id: str, unit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a specific unit.

        Args:
            unit_id: The UUID of the unit to update
            unit_data: Dictionary containing the unit properties to update

        Returns:
            JSON response containing the updated unit
        """
        if not unit_id:
            raise ValueError("Unit ID cannot be empty")
        if not unit_data:
            raise ValueError("Unit data cannot be empty")

        logger.info({"message": "Updating unit", "unit_id": unit_id})
        return self._handle_request("PUT", f"/api/units/{unit_id}", json=unit_data)

    def delete_unit(self, unit_id: str) -> Dict[str, Any]:
        """Delete a specific unit.

        Args:
            unit_id: The UUID of the unit to delete

        Returns:
            JSON response confirming deletion
        """
        if not unit_id:
            raise ValueError("Unit ID cannot be empty")

        logger.info({"message": "Deleting unit", "unit_id": unit_id})
        return self._handle_request("DELETE", f"/api/units/{unit_id}")
