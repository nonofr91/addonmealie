import logging
import os
from pathlib import Path


class CollectorConfig:
    def __init__(self) -> None:
        self.api_host = os.environ.get("PRICE_COLLECTOR_API_HOST", "0.0.0.0")
        self.api_port = int(os.environ.get("PRICE_COLLECTOR_API_PORT", "8004"))
        self.data_dir = Path(os.environ.get("PRICE_COLLECTOR_DATA_DIR", "data"))
        self.database_path = Path(
            os.environ.get("PRICE_COLLECTOR_DATABASE_PATH", str(self.data_dir / "prices.sqlite3"))
        )
        self.default_currency = os.environ.get("PRICE_COLLECTOR_DEFAULT_CURRENCY", "EUR")
        self.log_level = os.environ.get("LOG_LEVEL", "INFO")
        self.enable_drive_scraping = os.environ.get("ENABLE_DRIVE_SCRAPING", "false").lower() == "true"
        self.drive_cache_ttl_hours = int(os.environ.get("DRIVE_CACHE_TTL_HOURS", "24"))
        self.drive_rate_limit_delay = float(os.environ.get("DRIVE_RATE_LIMIT_DELAY", "1.0"))
        self._setup_logging()

    def _setup_logging(self) -> None:
        level = getattr(logging, self.log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def to_dict(self) -> dict:
        return {
            "api_host": self.api_host,
            "api_port": self.api_port,
            "data_dir": str(self.data_dir),
            "database_path": str(self.database_path),
            "default_currency": self.default_currency,
            "log_level": self.log_level,
            "enable_drive_scraping": self.enable_drive_scraping,
            "drive_cache_ttl_hours": self.drive_cache_ttl_hours,
            "drive_rate_limit_delay": self.drive_rate_limit_delay,
        }


_config: CollectorConfig | None = None


def get_config() -> CollectorConfig:
    global _config
    if _config is None:
        _config = CollectorConfig()
    return _config
