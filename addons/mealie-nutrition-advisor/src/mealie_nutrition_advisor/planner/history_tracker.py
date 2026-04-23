"""History tracker for menu variety — uses Mealie native mealplan API.

This module tracks recipe usage history via the native Mealie mealplan API,
eliminating the need for separate storage in the addon.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Optional

from ..mealie_sync import MealieClient
from ..models.menu import MealType

logger = logging.getLogger(__name__)

# Default history window for variety tracking (4 weeks as per spec)
DEFAULT_HISTORY_DAYS = 28

# Recipe families for variety tracking (prevent similar meals too close)
RECIPE_FAMILIES: dict[str, list[str]] = {
    "pasta": ["pasta", "spaghetti", "penne", "tagliatelle", "fettuccine", "lasagne", "ravioli", "gnocchi", "macaroni"],
    "rice": ["rice", "risotto", "paella", "pilaf", "riz"],
    "pizza": ["pizza", "tartiflette"],
    "soup": ["soup", "soupe", "velouté", "bisque", "minestrone", "potage", "bouillon"],
    "salad": ["salad", "salade", "taboulé"],
    "gratin": ["gratin", "dauphinois"],
    "stew": ["stew", "ragout", "braisé", "casserole", "cocotte", "ragoût"],
    "roast": ["roast", "rôti", "poulet rôti", "rotis"],
    "grilled": ["grilled", "grillé", "bbq", "barbecue", "plancha"],
    "stir_fry": ["stir fry", "wok", "sauté"],
    "curry": ["curry", "tikka", "massala"],
    "fish": ["fish", "poisson", "saumon", "cabillaud", "bar", "colin", "merlu", "sole"],
    "seafood": ["seafood", "fruits de mer", "moules", "huîtres", "crevettes", "gambas"],
    "egg_dish": ["omelette", "frittata", "quiche", "tortilla", "oeuf", "œuf"],
    "sandwich": ["sandwich", "burger", "tartine", "croque-monsieur", "wrap"],
    "tart": ["tart", "tarte", "quiche"],
    "bread_based": ["toast", "croque", "bruschetta", "crostini"],
    "legume": ["lentil", "lentille", "chickpea", "pois chiche", "bean", "haricot", "fève"],
}


class RecipeUsageRecord:
    """Record of a recipe usage in a mealplan."""
    
    def __init__(
        self,
        recipe_slug: str,
        recipe_name: str,
        recipe_id: Optional[str],
        used_date: date,
        meal_type: MealType,
    ) -> None:
        self.recipe_slug = recipe_slug
        self.recipe_name = recipe_name
        self.recipe_id = recipe_id
        self.used_date = used_date
        self.meal_type = meal_type
        self.days_ago: int = (date.today() - used_date).days


class VarietyMetrics:
    """Metrics for variety analysis of a menu."""
    
    def __init__(self) -> None:
        self.recipes_used_last_7_days: set[str] = set()
        self.recipes_used_last_14_days: set[str] = set()
        self.recipes_used_last_28_days: set[str] = set()
        self.family_usage_last_7_days: dict[str, int] = {}
        self.family_usage_last_14_days: dict[str, int] = {}
        self.family_usage_last_28_days: dict[str, int] = {}
    
    def is_recently_used(self, recipe_slug: str, days: int = 7) -> bool:
        """Check if a recipe was used in the last N days."""
        if days <= 7:
            return recipe_slug in self.recipes_used_last_7_days
        elif days <= 14:
            return recipe_slug in self.recipes_used_last_14_days
        else:
            return recipe_slug in self.recipes_used_last_28_days
    
    def get_family_usage_count(self, family: str, days: int = 7) -> int:
        """Get how many times a recipe family was used in the last N days."""
        if days <= 7:
            return self.family_usage_last_7_days.get(family, 0)
        elif days <= 14:
            return self.family_usage_last_14_days.get(family, 0)
        else:
            return self.family_usage_last_28_days.get(family, 0)


class HistoryTracker:
    """Tracks recipe usage history via Mealie native mealplan API.
    
    This class queries Mealie's mealplan API to build a history of recipe usage,
    enabling variety scoring without duplicating data in the addon.
    """
    
    def __init__(
        self,
        mealie_client: Optional[MealieClient] = None,
        history_days: int = DEFAULT_HISTORY_DAYS,
    ) -> None:
        self.client = mealie_client or MealieClient()
        self.history_days = history_days
        self._cache: Optional[list[RecipeUsageRecord]] = None
        self._cache_date: Optional[date] = None
        self._cache_duration = timedelta(hours=1)  # Cache for 1 hour
    
    def _is_cache_valid(self) -> bool:
        """Check if cached history is still valid."""
        if self._cache is None or self._cache_date is None:
            return False
        return (date.today() - self._cache_date) < self._cache_duration
    
    def _get_family(self, recipe_name: str) -> Optional[str]:
        """Determine the recipe family based on recipe name."""
        name_lower = recipe_name.lower()
        for family, keywords in RECIPE_FAMILIES.items():
            for keyword in keywords:
                if keyword.lower() in name_lower:
                    return family
        return None
    
    def fetch_history(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        use_cache: bool = True,
    ) -> list[RecipeUsageRecord]:
        """Fetch recipe usage history from Mealie mealplan API.
        
        Args:
            start_date: Start of history period (default: today - history_days)
            end_date: End of history period (default: today)
            use_cache: Whether to use cached results
            
        Returns:
            List of recipe usage records.
        """
        # Check cache
        if use_cache and self._is_cache_valid():
            logger.debug("Using cached history (%d records)", len(self._cache or []))
            return self._cache or []
        
        # Determine date range
        end = end_date or date.today()
        start = start_date or (end - timedelta(days=self.history_days))
        
        logger.info("Fetching mealplan history from %s to %s", start, end)
        
        records: list[RecipeUsageRecord] = []
        
        try:
            # Query Mealie mealplan API
            # Note: Mealie v3.x supports date range queries
            resp = self.client._client.get(
                f"{self.client.base_url}/api/households/mealplans",
                params={
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat(),
                    "perPage": 1000,  # Get all entries in range
                },
            )
            resp.raise_for_status()
            data = resp.json()
            
            items = data.get("items", [])
            logger.info("Retrieved %d mealplan entries from Mealie", len(items))
            
            for entry in items:
                entry_date_str = entry.get("date", "")
                try:
                    entry_date = date.fromisoformat(entry_date_str)
                except (ValueError, TypeError):
                    continue
                
                # Get recipe info
                recipe_id = entry.get("recipeId")
                recipe = entry.get("recipe")
                
                if recipe:
                    slug = recipe.get("slug", "")
                    name = recipe.get("name", slug)
                elif entry.get("title"):
                    # Title-only entry (no recipe linked)
                    slug = ""
                    name = entry.get("title", "")
                else:
                    continue
                
                # Determine meal type
                entry_type = entry.get("entryType", "dinner")
                try:
                    meal_type = MealType(entry_type.lower())
                except ValueError:
                    meal_type = MealType.dinner
                
                record = RecipeUsageRecord(
                    recipe_slug=slug,
                    recipe_name=name,
                    recipe_id=recipe_id,
                    used_date=entry_date,
                    meal_type=meal_type,
                )
                records.append(record)
            
            # Update cache
            self._cache = records
            self._cache_date = date.today()
            
        except Exception as exc:
            logger.error("Failed to fetch mealplan history: %s", exc)
            # Return empty list on error, don't cache
            return []
        
        return records
    
    def compute_variety_metrics(
        self,
        days: int = DEFAULT_HISTORY_DAYS,
    ) -> VarietyMetrics:
        """Compute variety metrics from history.
        
        Args:
            days: Number of days to analyze (default: 28)
            
        Returns:
            VarietyMetrics with usage counts by period.
        """
        end = date.today()
        start = end - timedelta(days=days)
        
        records = self.fetch_history(start_date=start, end_date=end)
        
        metrics = VarietyMetrics()
        
        for record in records:
            slug = record.recipe_slug
            if not slug:
                continue
            
            # Track recipe usage by time window
            if record.days_ago <= 7:
                metrics.recipes_used_last_7_days.add(slug)
                metrics.recipes_used_last_14_days.add(slug)
                metrics.recipes_used_last_28_days.add(slug)
            elif record.days_ago <= 14:
                metrics.recipes_used_last_14_days.add(slug)
                metrics.recipes_used_last_28_days.add(slug)
            elif record.days_ago <= 28:
                metrics.recipes_used_last_28_days.add(slug)
            
            # Track family usage
            family = self._get_family(record.recipe_name)
            if family:
                if record.days_ago <= 7:
                    metrics.family_usage_last_7_days[family] = \
                        metrics.family_usage_last_7_days.get(family, 0) + 1
                    metrics.family_usage_last_14_days[family] = \
                        metrics.family_usage_last_14_days.get(family, 0) + 1
                    metrics.family_usage_last_28_days[family] = \
                        metrics.family_usage_last_28_days.get(family, 0) + 1
                elif record.days_ago <= 14:
                    metrics.family_usage_last_14_days[family] = \
                        metrics.family_usage_last_14_days.get(family, 0) + 1
                    metrics.family_usage_last_28_days[family] = \
                        metrics.family_usage_last_28_days.get(family, 0) + 1
                elif record.days_ago <= 28:
                    metrics.family_usage_last_28_days[family] = \
                        metrics.family_usage_last_28_days.get(family, 0) + 1
        
        logger.debug(
            "Variety metrics: %d unique recipes last 7d, %d last 28d, families: %s",
            len(metrics.recipes_used_last_7_days),
            len(metrics.recipes_used_last_28_days),
            dict(metrics.family_usage_last_7_days),
        )
        
        return metrics
    
    def get_last_used_date(self, recipe_slug: str) -> Optional[date]:
        """Get the last date a recipe was used.
        
        Args:
            recipe_slug: Recipe slug to check
            
        Returns:
            Last usage date or None if never used.
        """
        records = self.fetch_history()
        
        for record in records:
            if record.recipe_slug == recipe_slug:
                return record.used_date
        
        return None
    
    def days_since_last_used(self, recipe_slug: str) -> Optional[int]:
        """Get number of days since a recipe was last used.
        
        Args:
            recipe_slug: Recipe slug to check
            
        Returns:
            Days since last use, or None if never used.
        """
        last_date = self.get_last_used_date(recipe_slug)
        if last_date:
            return (date.today() - last_date).days
        return None
    
    def invalidate_cache(self) -> None:
        """Invalidate the history cache (call after pushing new menus)."""
        self._cache = None
        self._cache_date = None
        logger.debug("History cache invalidated")
    
    def close(self) -> None:
        """Close the Mealie client connection."""
        self.client.close()
    
    def __enter__(self) -> "HistoryTracker":
        return self
    
    def __exit__(self, *args) -> None:
        self.close()
