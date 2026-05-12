"""Configuration centralisée du Budget Advisor."""

import logging
import os
from pathlib import Path
from typing import Optional


class BudgetConfigError(Exception):
    """Erreur de configuration."""

    pass


class BudgetConfig:
    """Configuration singleton pour le Budget Advisor."""

    _instance: Optional["BudgetConfig"] = None

    def __new__(cls) -> "BudgetConfig":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        # Mealie connection
        self.mealie_base_url = os.environ.get(
            "MEALIE_BASE_URL", "http://localhost:9925"
        ).rstrip("/")
        self.mealie_api_key = os.environ.get("MEALIE_API_KEY", "")

        if not self.mealie_api_key:
            raise BudgetConfigError(
                "MEALIE_API_KEY est requis. "
                "Créez un token dans Mealie (Admin > API Tokens)."
            )

        # API Server
        self.api_host = os.environ.get("ADDON_API_HOST", "0.0.0.0")
        self.api_port = int(os.environ.get("ADDON_API_PORT", "8003"))
        self.secret_key = os.environ.get("ADDON_SECRET_KEY", "change-me-in-production")

        # UI Server
        self.ui_port = int(os.environ.get("ADDON_UI_PORT", "8503"))
        self.api_url = os.environ.get("ADDON_API_URL", f"http://localhost:{self.api_port}")

        # Price Collector (addon interne)
        self.price_collector_url = os.environ.get("PRICE_COLLECTOR_URL", "").rstrip("/")

        # Open Prices
        self.open_prices_base_url = os.environ.get(
            "OPEN_PRICES_BASE_URL", "https://prices.openfoodfacts.org/api/v1"
        ).rstrip("/")

        # Feature flags
        self._enable_open_prices = (
            os.environ.get("ENABLE_OPEN_PRICES", "true").lower() == "true"
        )
        self._enable_manual_prices = (
            os.environ.get("ENABLE_MANUAL_PRICES", "true").lower() == "true"
        )
        self._enable_budget_planning = (
            os.environ.get("ENABLE_BUDGET_PLANNING", "true").lower() == "true"
        )

        # Rafraîchissement mensuel automatique des coûts (publication dans extras)
        self._enable_monthly_cost_refresh = (
            os.environ.get("ENABLE_MONTHLY_COST_REFRESH", "true").lower() == "true"
        )
        self._monthly_cost_refresh_cron = os.environ.get(
            "MONTHLY_COST_REFRESH_CRON", "0 3 1 * *"
        ).strip()

        # Data paths - use absolute paths for Docker volume mounts
        self.data_dir = Path("/app/data")
        self.config_dir = Path("/app/config")

        # Logs
        self.log_level = os.environ.get("LOG_LEVEL", "INFO")
        self._setup_logging()

        self._initialized = True

    def _setup_logging(self) -> None:
        """Configure le logging."""
        level = getattr(logging, self.log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    @property
    def enable_open_prices(self) -> bool:
        return self._enable_open_prices

    @property
    def enable_manual_prices(self) -> bool:
        return self._enable_manual_prices

    @property
    def enable_budget_planning(self) -> bool:
        return self._enable_budget_planning

    @property
    def enable_monthly_cost_refresh(self) -> bool:
        return self._enable_monthly_cost_refresh

    @property
    def monthly_cost_refresh_cron(self) -> str:
        return self._monthly_cost_refresh_cron

    def to_dict(self) -> dict:
        """Retourne la configuration sans secrets."""
        return {
            "mealie_base_url": self.mealie_base_url,
            "api_host": self.api_host,
            "api_port": self.api_port,
            "ui_port": self.ui_port,
            "api_url": self.api_url,
            "price_collector_url": self.price_collector_url or "(non configuré)",
            "open_prices_base_url": self.open_prices_base_url,
            "enable_open_prices": self.enable_open_prices,
            "enable_manual_prices": self.enable_manual_prices,
            "enable_budget_planning": self.enable_budget_planning,
            "enable_monthly_cost_refresh": self.enable_monthly_cost_refresh,
            "monthly_cost_refresh_cron": self.monthly_cost_refresh_cron,
            "log_level": self.log_level,
        }


def get_config() -> BudgetConfig:
    """Retourne l'instance de configuration."""
    return BudgetConfig()
