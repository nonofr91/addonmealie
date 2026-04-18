"""Configuration management for mealie-nutrition-advisor addon."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()


class NutritionConfigError(Exception):
    """Configuration error for nutrition addon."""


class NutritionConfig:
    """Configuration for mealie-nutrition-advisor addon."""

    def __init__(self) -> None:
        self._mealie_base_url = os.environ.get("MEALIE_BASE_URL", "")
        self._mealie_api_key = os.environ.get("MEALIE_API_KEY", "")
        self._ai_provider = os.environ.get("AI_PROVIDER", "mock")
        self._use_ai_estimation = os.environ.get("USE_AI_ESTIMATION", "false").lower() == "true"
        
        # AI provider keys
        self._openai_api_key = os.environ.get("OPENAI_API_KEY", "")
        self._openai_model = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
        self._anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self._anthropic_model = os.environ.get("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
        self._mistral_api_key = os.environ.get("MISTRAL_API_KEY", "")
        self._mistral_model = os.environ.get("MISTRAL_MODEL", "mistral-small-latest")
        
        # Open Food Facts
        self._off_base_url = os.environ.get("OFF_BASE_URL", "https://world.openfoodfacts.org")
        
        # Cache
        self._cache_ttl_days = int(os.environ.get("NUTRITION_CACHE_TTL_DAYS", "30"))
        
        # API server config
        self._api_host = os.environ.get("ADDON_API_HOST", "0.0.0.0")
        self._api_port = int(os.environ.get("ADDON_API_PORT", "8001"))
        self._api_secret_key = os.environ.get("ADDON_SECRET_KEY", "")
        
        # UI server config
        self._ui_port = int(os.environ.get("ADDON_UI_PORT", "8502"))
        
        self._validate()

    def _validate(self) -> None:
        """Validate required configuration."""
        if not self._mealie_base_url:
            raise NutritionConfigError("MEALIE_BASE_URL is required")
        if not self._mealie_api_key:
            raise NutritionConfigError("MEALIE_API_KEY is required")

    @property
    def mealie_base_url(self) -> str:
        return self._mealie_base_url.rstrip("/")

    @property
    def mealie_api_key(self) -> str:
        return self._mealie_api_key

    @property
    def ai_provider(self) -> str:
        return self._ai_provider

    @property
    def use_ai_estimation(self) -> bool:
        return self._use_ai_estimation

    @property
    def openai_api_key(self) -> str:
        return self._openai_api_key

    @property
    def openai_model(self) -> str:
        return self._openai_model

    @property
    def anthropic_api_key(self) -> str:
        return self._anthropic_api_key

    @property
    def anthropic_model(self) -> str:
        return self._anthropic_model

    @property
    def mistral_api_key(self) -> str:
        return self._mistral_api_key

    @property
    def mistral_model(self) -> str:
        return self._mistral_model

    @property
    def off_base_url(self) -> str:
        return self._off_base_url

    @property
    def cache_ttl_days(self) -> int:
        return self._cache_ttl_days

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

    @classmethod
    def load(cls) -> "NutritionConfig":
        """Load configuration from environment variables."""
        return cls()
