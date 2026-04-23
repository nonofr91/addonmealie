"""Manual price database — JSON-backed CRUD for user-curated prices."""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path
from typing import Iterable, Optional

from ..models.pricing import ManualPrice, PriceSource

logger = logging.getLogger(__name__)


def _normalize(name: str) -> str:
    return name.strip().lower()


class ManualPricer:
    """JSON-backed storage for user-curated ingredient prices.

    Shape on disk: {ingredient_name: {unit, price_per_unit, currency, source, note, updated_at}}.
    """

    def __init__(self, data_path: Path) -> None:
        self.data_path = Path(data_path)
        self._cache: dict[str, ManualPrice] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        if self.data_path.exists():
            try:
                raw = json.loads(self.data_path.read_text(encoding="utf-8"))
                for name, payload in raw.items():
                    payload = dict(payload)
                    payload.setdefault("ingredient_name", name)
                    payload.setdefault("source", PriceSource.manual.value)
                    self._cache[_normalize(name)] = ManualPrice.model_validate(payload)
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to load manual prices from %s: %s", self.data_path, exc)
                self._cache = {}
        self._loaded = True

    def _save(self) -> None:
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {name: price.model_dump(mode="json") for name, price in self._cache.items()}
        self.data_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def list(self) -> list[ManualPrice]:
        self._ensure_loaded()
        return sorted(self._cache.values(), key=lambda p: p.ingredient_name)

    def get(self, name: str) -> Optional[ManualPrice]:
        self._ensure_loaded()
        return self._cache.get(_normalize(name))

    def upsert(self, price: ManualPrice) -> ManualPrice:
        self._ensure_loaded()
        price.ingredient_name = _normalize(price.ingredient_name)
        if not price.updated_at:
            price.updated_at = date.today()
        self._cache[price.ingredient_name] = price
        self._save()
        return price

    def delete(self, name: str) -> bool:
        self._ensure_loaded()
        key = _normalize(name)
        if key in self._cache:
            del self._cache[key]
            self._save()
            return True
        return False

    def bulk_upsert(self, prices: Iterable[ManualPrice]) -> int:
        count = 0
        for price in prices:
            self.upsert(price)
            count += 1
        return count
