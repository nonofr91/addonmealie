"""Configuration management for mealie-budget-advisor addon."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class BudgetConfigError(Exception):
    """Configuration error for budget addon."""


class BudgetConfig:
    """Configuration for mealie-budget-advisor addon."""

    def __init__(self) -> None:
        self._mealie_base_url = os.environ.get("MEALIE_BASE_URL", "")
        self._mealie_api_key = os.environ.get("MEALIE_API_KEY", "")

        # Open Prices
        self._open_prices_base_url = os.environ.get(
            "OPEN_PRICES_BASE_URL", "https://prices.openfoodfacts.org/api/v1"
        )
        self._off_base_url = os.environ.get(
            "OFF_BASE_URL", "https://world.openfoodfacts.org"
        )

        # API/UI
        self._api_host = os.environ.get("ADDON_API_HOST", "0.0.0.0")
        self._api_port = int(os.environ.get("ADDON_API_PORT", "8003"))
        self._api_secret_key = os.environ.get("ADDON_SECRET_KEY", "")
        self._ui_port = int(os.environ.get("ADDON_UI_PORT", "8503"))

        # Optional integration with nutrition addon
        self._nutrition_api_url = os.environ.get("NUTRITION_API_URL", "").rstrip("/")

        # Feature flags
        self._enable_open_prices = os.environ.get("ENABLE_OPEN_PRICES", "true").lower() == "true"
        self._enable_manual_prices = os.environ.get("ENABLE_MANUAL_PRICES", "true").lower() == "true"
        self._enable_budget_planning = os.environ.get("ENABLE_BUDGET_PLANNING", "true").lower() == "true"

        # Rafraîchissement mensuel des coûts dans Mealie (extras.cout_*)
        self._enable_monthly_cost_refresh = (
            os.environ.get("ENABLE_MONTHLY_COST_REFRESH", "true").lower() == "true"
        )
        # Expression cron standard à 5 champs (minute heure jour mois jour-semaine)
        self._monthly_cost_refresh_cron = os.environ.get(
            "MONTHLY_COST_REFRESH_CRON", "0 3 1 * *"
        )

        # Data paths — all stateful files live in project-relative data/ & config/
        pkg_root = Path(__file__).resolve().parent.parent.parent
        self._data_dir = Path(os.environ.get("BUDGET_DATA_DIR", pkg_root / "data"))
        self._config_dir = Path(os.environ.get("BUDGET_CONFIG_DIR", pkg_root / "config"))

        self._validate()

    def _validate(self) -> None:
        if not self._mealie_base_url:
            raise BudgetConfigError("MEALIE_BASE_URL is required")
        if not self._mealie_api_key:
            raise BudgetConfigError("MEALIE_API_KEY is required")

    @property
    def mealie_base_url(self) -> str:
        return self._mealie_base_url.rstrip("/")

    @property
    def mealie_api_key(self) -> str:
        return self._mealie_api_key

    @property
    def open_prices_base_url(self) -> str:
        return self._open_prices_base_url.rstrip("/")

    @property
    def off_base_url(self) -> str:
        return self._off_base_url.rstrip("/")

    @property
    def api_host(self) -> str:
        return self._api_host

    @property
    def api_port(self) -> int:
        return self._api_port

    @property
    def api_secret_key(self) -> str:
        return self._api_secret_key

    @property
    def ui_port(self) -> int:
        return self._ui_port

    @property
    def nutrition_api_url(self) -> str:
        return self._nutrition_api_url

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

    @property
    def data_dir(self) -> Path:
        return self._data_dir

    @property
    def config_dir(self) -> Path:
        return self._config_dir

    @classmethod
    def load(cls) -> "BudgetConfig":
        return cls()
