import logging
from datetime import date, datetime, timezone
from typing import Any

import requests

from ..models import PriceObservation, PriceSource

logger = logging.getLogger(__name__)


class OpenPricesCollector:
    BASE_URL = "https://prices.openfoodfacts.org/api/v1"

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or self.BASE_URL).rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "Ingredient-Price-Collector/0.1.0",
        })

    def search(
        self,
        query: str,
        limit: int = 10,
        currency: str = "EUR",
    ) -> list[PriceObservation]:
        params: dict[str, Any] = {
            "product_name__like": query,
            "currency": currency,
            "page": 1,
            "size": limit,
        }

        try:
            response = self.session.get(
                f"{self.base_url}/prices",
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            observations = []
            for item in data.get("items", []):
                observation = self._parse_to_observation(item, query)
                if observation:
                    observations.append(observation)

            logger.debug(f"Open Prices: {len(observations)} observations pour '{query}'")
            return observations

        except requests.exceptions.RequestException as exc:
            logger.warning(f"Erreur Open Prices pour '{query}': {exc}")
            return []

    def _parse_to_observation(self, item: dict, original_query: str) -> PriceObservation | None:
        try:
            product = item.get("product", {})
            product_name = product.get("product_name") or product.get("name", "Unknown")
            price_amount = float(item.get("price", 0))
            quantity = float(item.get("quantity", 1) or 1)
            unit = item.get("quantity_unit", "unit")
            currency = item.get("currency", "EUR")

            if price_amount <= 0 or quantity <= 0:
                logger.debug(f"Prix invalide ignoré: {product_name} - {price_amount}/{quantity}{unit}")
                return None

            location = item.get("location", {})
            store_name = location.get("name") if isinstance(location, dict) else None
            store_location = location.get("address") if isinstance(location, dict) else None

            observed_at_str = item.get("date")
            observed_at = None
            if observed_at_str:
                try:
                    observed_at = date.fromisoformat(observed_at_str[:10])
                except (ValueError, TypeError):
                    pass

            return PriceObservation(
                ingredient_name=original_query,
                normalized_ingredient=original_query.lower(),
                product_name=product_name,
                barcode=product.get("code"),
                source=PriceSource.open_prices,
                source_url=item.get("proof_url"),
                store_name=store_name,
                store_location=store_location,
                observed_at=observed_at,
                price_amount=price_amount,
                currency=currency,
                package_quantity=quantity,
                package_unit=unit,
                confidence=0.7,
                quality_flags=[],
                raw_payload=item,
                created_at=datetime.now(timezone.utc),
            )

        except (KeyError, ValueError, TypeError) as exc:
            logger.debug(f"Erreur parsing item Open Prices: {exc}")
            return None

    def health_check(self) -> bool:
        try:
            response = self.session.get(f"{self.base_url}/status", timeout=10)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
