"""Persist/load monthly budget settings."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from .models.budget import BudgetSettings

logger = logging.getLogger(__name__)


class BudgetManager:
    """Persistence layer for monthly budget settings.

    Stored as a flat JSON map: {"YYYY-MM": <BudgetSettings>}.
    """

    def __init__(self, config_path: Path) -> None:
        self.config_path = Path(config_path)
        self._cache: dict[str, BudgetSettings] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        if self.config_path.exists():
            try:
                raw = json.loads(self.config_path.read_text(encoding="utf-8"))
                for month, payload in raw.items():
                    self._cache[month] = BudgetSettings.model_validate(payload)
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to load budget settings from %s: %s", self.config_path, exc)
                self._cache = {}
        self._loaded = True

    def _save(self) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {m: s.model_dump(mode="json") for m, s in self._cache.items()}
        self.config_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def list(self) -> dict[str, BudgetSettings]:
        self._ensure_loaded()
        return dict(self._cache)

    def get(self, month: str) -> Optional[BudgetSettings]:
        self._ensure_loaded()
        return self._cache.get(month)

    def get_or_default(self, month: str) -> BudgetSettings:
        settings = self.get(month)
        if settings:
            return settings
        # Sensible default when nothing is configured yet (forfait forced to 0 to
        # keep `condiments_forfait <= total_budget` invariant).
        return BudgetSettings(month=month, total_budget=0.0, condiments_forfait=0.0)

    def set(self, settings: BudgetSettings) -> BudgetSettings:
        self._ensure_loaded()
        self._cache[settings.month] = settings
        self._save()
        logger.info("Budget saved for %s: %.2f%s", settings.month, settings.total_budget, settings.currency)
        return settings

    def delete(self, month: str) -> bool:
        self._ensure_loaded()
        if month in self._cache:
            del self._cache[month]
            self._save()
            return True
        return False
