import logging
import time
from datetime import datetime, timezone

from ..config import get_config
from ..models import PriceObservation, PriceSource
from ..storage import PriceStorage

logger = logging.getLogger(__name__)


class DriveCollector:
    def __init__(self, storage: PriceStorage) -> None:
        self.storage = storage
        self.config = get_config()

    def collect(self, ingredient: str, store: str | None = None) -> list[PriceObservation]:
        if not self.config.enable_drive_scraping:
            logger.warning("Drive scraping is disabled (ENABLE_DRIVE_SCRAPING=false)")
            return []

        cache_key = f"drive:{ingredient}:{store or 'all'}"
        cached = self.storage.cache_get(cache_key)
        if cached:
            logger.debug(f"Drive cache hit for {ingredient}")
            return [PriceObservation(**item) for item in cached.get("observations", [])]

        logger.info(f"Drive scraping for {ingredient} (cache miss)")
        time.sleep(self.config.drive_rate_limit_delay)

        observations = self._mock_drive_scrape(ingredient, store)
        if observations:
            self.storage.cache_set(
                cache_key,
                {"observations": [obs.model_dump() for obs in observations]},
                ttl_hours=self.config.drive_cache_ttl_hours,
            )

        return observations

    def _mock_drive_scrape(self, ingredient: str, store: str | None) -> list[PriceObservation]:
        logger.warning("Drive scraping is not implemented (mock only)")
        return []

    def health_check(self) -> bool:
        return self.config.enable_drive_scraping
