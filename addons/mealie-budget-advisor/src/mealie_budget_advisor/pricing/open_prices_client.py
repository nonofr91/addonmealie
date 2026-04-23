"""Client for the Open Prices API (Open Food Facts)."""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from ..models.pricing import OpenPrice, PriceSource

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15.0


class OpenPricesClient:
    """Thin HTTP client for the Open Prices API.

    Endpoint: GET {base}/prices
    Documented params include `product_code`, `product_name_like`, `page`, `size`.
    This client only issues public GETs, no authentication required.
    """

    def __init__(self, base_url: str, timeout: float = REQUEST_TIMEOUT) -> None:
        self.base_url = base_url.rstrip("/")
        self._timeout = timeout

    def _client(self) -> httpx.Client:
        return httpx.Client(timeout=self._timeout)

    def search_by_name(self, query: str, size: int = 10) -> list[OpenPrice]:
        """Search recent prices by fuzzy product name."""
        if not query.strip():
            return []
        params = {"product_name_like": query, "size": size, "order_by": "-created"}
        return self._query(params)

    def search_by_barcode(self, barcode: str, size: int = 10) -> list[OpenPrice]:
        """Search recent prices by product barcode (EAN)."""
        if not barcode.strip():
            return []
        params = {"product_code": barcode, "size": size, "order_by": "-created"}
        return self._query(params)

    def _query(self, params: dict[str, Any]) -> list[OpenPrice]:
        url = f"{self.base_url}/prices"
        try:
            with self._client() as client:
                resp = client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            logger.warning("Open Prices query failed for %s: %s", params, exc)
            return []

        items = data.get("items", []) if isinstance(data, dict) else []
        out: list[OpenPrice] = []
        for raw in items:
            price = self._to_model(raw)
            if price is not None:
                out.append(price)
        return out

    @staticmethod
    def _to_model(raw: dict[str, Any]) -> Optional[OpenPrice]:
        try:
            price_value = raw.get("price")
            if price_value is None:
                return None
            product = raw.get("product") or {}
            location = raw.get("location") or {}
            return OpenPrice(
                product_name=product.get("product_name") or raw.get("product_name"),
                product_code=raw.get("product_code") or product.get("code"),
                price=float(price_value),
                currency=raw.get("currency") or "EUR",
                store=(raw.get("proof") or {}).get("location_osm_display_name")
                or location.get("osm_display_name"),
                location=location.get("osm_display_name"),
                collected_at=None,  # Open Prices returns ISO string; leave unparsed for now.
                source=PriceSource.open_prices,
            )
        except (TypeError, ValueError) as exc:
            logger.debug("Skipping malformed Open Prices item: %s (%s)", raw, exc)
            return None

    @staticmethod
    def median_price(prices: list[OpenPrice]) -> Optional[float]:
        """Return median price value from a list, or None if empty."""
        values = sorted(p.price for p in prices)
        if not values:
            return None
        mid = len(values) // 2
        if len(values) % 2 == 1:
            return values[mid]
        return (values[mid - 1] + values[mid]) / 2
