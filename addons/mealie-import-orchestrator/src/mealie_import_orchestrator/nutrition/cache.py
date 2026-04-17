"""Local JSON cache for nutrition lookups — avoids repeated OFF API calls."""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ..models.nutrition import NutritionFacts

logger = logging.getLogger(__name__)

DEFAULT_CACHE_PATH = Path(__file__).parent.parent.parent.parent / "data" / "nutrition_cache.json"
TTL_DAYS = int(os.environ.get("NUTRITION_CACHE_TTL_DAYS", "30"))


def _normalize_key(name: str) -> str:
    """Normalise un nom d'ingrédient en clé de cache."""
    return re.sub(r"\s+", " ", name.lower().strip())


class NutritionCache:
    """Cache JSON persistant pour les données nutritionnelles par 100g."""

    def __init__(self, cache_path: Path | None = None, ttl_days: int = TTL_DAYS) -> None:
        self.cache_path = Path(cache_path) if cache_path else DEFAULT_CACHE_PATH
        self.ttl_days = ttl_days
        self._data: dict[str, dict] = {}
        self._dirty = False
        self._load()

    def _load(self) -> None:
        if self.cache_path.exists():
            try:
                raw = json.loads(self.cache_path.read_text(encoding="utf-8"))
                self._data = raw.get("entries", {})
                logger.debug("Cache nutritionnel chargé: %d entrées", len(self._data))
            except Exception as exc:
                logger.warning("Erreur lecture cache: %s — cache réinitialisé", exc)
                self._data = {}

    def save(self) -> None:
        if not self._dirty:
            return
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"entries": self._data, "updated_at": datetime.now(timezone.utc).isoformat()}
        self.cache_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        self._dirty = False
        logger.debug("Cache nutritionnel sauvegardé: %d entrées", len(self._data))

    def get(self, ingredient_name: str) -> Optional[NutritionFacts]:
        """Retourne les données cachées si elles existent et ne sont pas expirées."""
        key = _normalize_key(ingredient_name)
        entry = self._data.get(key)
        if entry is None:
            return None

        cached_at_str = entry.get("cached_at", "")
        try:
            cached_at = datetime.fromisoformat(cached_at_str)
            age_days = (datetime.now(timezone.utc) - cached_at).days
            if age_days > self.ttl_days:
                logger.debug("Cache expiré pour '%s' (%d jours)", ingredient_name, age_days)
                del self._data[key]
                self._dirty = True
                return None
        except (ValueError, TypeError):
            pass

        try:
            facts = NutritionFacts.model_validate(entry["nutrition"])
            logger.debug("Cache HIT pour '%s'", ingredient_name)
            return facts
        except Exception as exc:
            logger.warning("Cache corrompu pour '%s': %s", ingredient_name, exc)
            return None

    def set(self, ingredient_name: str, facts: NutritionFacts, typical_weight_g: Optional[float] = None) -> None:
        """Sauvegarde les données nutritionnelles dans le cache."""
        key = _normalize_key(ingredient_name)
        entry = {
            "nutrition": facts.model_dump(),
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "original_name": ingredient_name,
        }
        if typical_weight_g is not None:
            entry["typical_weight_g"] = typical_weight_g
        self._data[key] = entry
        self._dirty = True
        logger.debug("Cache SET pour '%s' (poids moyen: %s g)", ingredient_name, typical_weight_g or "N/A")

    def __len__(self) -> int:
        return len(self._data)
