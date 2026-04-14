import logging
from typing import Any, Dict, List, Optional

from utils import format_api_params

logger = logging.getLogger("mealie-mcp")


class FoodsMixin:
    """Mixin class for food-related API endpoints"""

    def get_foods(
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
        """Get all foods.

        Args:
            page: Page number to retrieve
            per_page: Number of items per page
            order_by: Field to order results by
            order_direction: Direction to order results ('asc' or 'desc')
            search: Search term to filter foods
            query_filter: Advanced query filter
            order_by_null_position: How to handle nulls in ordering ('first' or 'last')
            pagination_seed: Seed for consistent pagination

        Returns:
            JSON response containing food items and pagination information
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

        logger.info({"message": "Retrieving foods", "parameters": params})
        return self._handle_request("GET", "/api/foods", params=params)

    def search_foods_by_name(self, name: str, page: Optional[int] = None, per_page: Optional[int] = None) -> Dict[str, Any]:
        """Search foods by name.

        Args:
            name: Food name to search for
            page: Page number to retrieve
            per_page: Number of items per page

        Returns:
            JSON response containing matching foods
        """
        if not name:
            raise ValueError("Food name cannot be empty")

        param_dict = {
            "search": name,
            "page": page,
            "perPage": per_page,
        }

        params = format_api_params(param_dict)

        logger.info({"message": "Searching foods by name", "name": name})
        return self._handle_request("GET", "/api/foods", params=params)

    def get_food(self, food_id: str) -> Dict[str, Any]:
        """Get a specific food by ID.

        Args:
            food_id: The UUID of the food

        Returns:
            JSON response containing the food details
        """
        if not food_id:
            raise ValueError("Food ID cannot be empty")

        logger.info({"message": "Retrieving food", "food_id": food_id})
        return self._handle_request("GET", f"/api/foods/{food_id}")

    def create_food(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new food.

        Args:
            name: Name of the food
            description: Optional description

        Returns:
            JSON response containing the created food
        """
        if not name:
            raise ValueError("Food name cannot be empty")

        payload = {"name": name}
        if description:
            payload["description"] = description

        logger.info({"message": "Creating food", "name": name})
        return self._handle_request("POST", "/api/foods", json=payload)

    def update_food(self, food_id: str, food_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a specific food.

        Args:
            food_id: The UUID of the food to update
            food_data: Dictionary containing the food properties to update

        Returns:
            JSON response containing the updated food
        """
        if not food_id:
            raise ValueError("Food ID cannot be empty")
        if not food_data:
            raise ValueError("Food data cannot be empty")

        logger.info({"message": "Updating food", "food_id": food_id})
        return self._handle_request("PUT", f"/api/foods/{food_id}", json=food_data)

    def delete_food(self, food_id: str) -> Dict[str, Any]:
        """Delete a specific food.

        Args:
            food_id: The UUID of the food to delete

        Returns:
            JSON response confirming deletion
        """
        if not food_id:
            raise ValueError("Food ID cannot be empty")

        logger.info({"message": "Deleting food", "food_id": food_id})
        return self._handle_request("DELETE", f"/api/foods/{food_id}")
