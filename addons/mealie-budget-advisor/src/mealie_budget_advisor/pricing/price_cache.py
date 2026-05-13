"""Cache layer for price lookups to reduce redundant API calls."""

import logging
import time
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with value and expiration."""
    value: Any
    expires_at: float


class PriceCache:
    """Simple in-memory cache for price lookups with TTL support."""

    def __init__(self):
        """Initialize the cache."""
        self._cache: dict[str, CacheEntry] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
        }

    def _make_key(self, source: str, ingredient_name: str) -> str:
        """Generate a cache key.

        Args:
            source: Price source (manual, open_prices, price_collector)
            ingredient_name: Normalized ingredient name

        Returns:
            Cache key
        """
        return f"{source}:{ingredient_name.lower()}"

    def get(self, source: str, ingredient_name: str) -> Optional[Any]:
        """Get a cached value if not expired.

        Args:
            source: Price source
            ingredient_name: Ingredient name

        Returns:
            Cached value or None if not found/expired
        """
        key = self._make_key(source, ingredient_name)
        entry = self._cache.get(key)

        if entry is None:
            self._stats["misses"] += 1
            return None

        if time.time() > entry.expires_at:
            # Entry expired, remove it
            del self._cache[key]
            self._stats["misses"] += 1
            return None

        self._stats["hits"] += 1
        logger.debug(f"Cache hit: {key}")
        return entry.value

    def set(
        self,
        source: str,
        ingredient_name: str,
        value: Any,
        ttl_seconds: int = 3600,
    ) -> None:
        """Set a cached value with TTL.

        Args:
            source: Price source
            ingredient_name: Ingredient name
            value: Value to cache
            ttl_seconds: Time to live in seconds
        """
        key = self._make_key(source, ingredient_name)
        expires_at = time.time() + ttl_seconds
        self._cache[key] = CacheEntry(value=value, expires_at=expires_at)
        self._stats["sets"] += 1
        logger.debug(f"Cache set: {key} (TTL: {ttl_seconds}s)")

    def invalidate(self, source: Optional[str] = None) -> None:
        """Invalidate cache entries.

        Args:
            source: If provided, only invalidate entries for this source.
                    If None, invalidate all entries.
        """
        if source is None:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cache cleared: {count} entries")
        else:
            keys_to_remove = [k for k in self._cache if k.startswith(f"{source}:")]
            for key in keys_to_remove:
                del self._cache[key]
            logger.info(f"Cache invalidated for source {source}: {len(keys_to_remove)} entries")

    def get_stats(self) -> dict[str, int]:
        """Get cache statistics.

        Returns:
            Dictionary with hit rate and counts
        """
        total_lookups = self._stats["hits"] + self._stats["misses"]
        hit_rate = (
            self._stats["hits"] / total_lookups if total_lookups > 0 else 0.0
        )
        return {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "sets": self._stats["sets"],
            "size": len(self._cache),
            "hit_rate": hit_rate,
        }

    def cleanup_expired(self) -> int:
        """Remove expired entries from cache.

        Returns:
            Number of entries removed
        """
        now = time.time()
        keys_to_remove = [
            k for k, v in self._cache.items() if now > v.expires_at
        ]
        for key in keys_to_remove:
            del self._cache[key]
        if keys_to_remove:
            logger.info(f"Cleaned up {len(keys_to_remove)} expired cache entries")
        return len(keys_to_remove)
