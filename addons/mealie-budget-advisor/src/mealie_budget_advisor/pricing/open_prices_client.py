"""Client pour l'API Open Prices (Open Food Facts)."""

import logging
from typing import Any, Optional

import requests

from ..models.pricing import OpenPrice

logger = logging.getLogger(__name__)


class OpenPricesClient:
    """Client pour récupérer les prix depuis Open Prices API."""

    BASE_URL = "https://prices.openfoodfacts.org/api/v1"

    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = (base_url or self.BASE_URL).rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "Mealie-Budget-Advisor/0.1.0",
        })

    def search_prices(
        self,
        query: str,
        limit: int = 10,
        currency: str = "EUR",
    ) -> list[OpenPrice]:
        """Recherche des prix par nom de produit.

        Args:
            query: Nom du produit à rechercher
            limit: Nombre max de résultats
            currency: Devise filtrée

        Returns:
            Liste des prix trouvés
        """
        try:
            params: dict[str, Any] = {
                "product_name__like": query,
                "currency": currency,
                "page": 1,
                "size": limit,
            }

            response = self.session.get(
                f"{self.base_url}/prices",
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            prices = []
            for item in data.get("items", []):
                price = self._parse_price_item(item)
                if price:
                    prices.append(price)

            logger.debug(f"Open Prices: {len(prices)} résultats pour '{query}'")
            return prices

        except requests.exceptions.RequestException as e:
            logger.warning(f"Erreur Open Prices pour '{query}': {e}")
            return []

    def get_price_by_barcode(
        self,
        barcode: str,
        currency: str = "EUR",
    ) -> Optional[OpenPrice]:
        """Récupère le prix par code-barres EAN.

        Args:
            barcode: Code EAN/GTIN
            currency: Devise filtrée

        Returns:
            Prix trouvé ou None
        """
        try:
            params: dict[str, Any] = {
                "product_code": barcode,
                "currency": currency,
                "page": 1,
                "size": 1,
            }

            response = self.session.get(
                f"{self.base_url}/prices",
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            items = data.get("items", [])
            if items:
                return self._parse_price_item(items[0])
            return None

        except requests.exceptions.RequestException as e:
            logger.warning(f"Erreur Open Prices pour barcode {barcode}: {e}")
            return None

    def _parse_price_item(self, item: dict) -> Optional[OpenPrice]:
        """Parse un item de l'API Open Prices."""
        try:
            product = item.get("product", {})

            # Vérifier que les champs requis sont présents
            quantity = item.get("quantity")
            quantity_unit = item.get("quantity_unit")
            price = item.get("price")

            # Ignorer les prix sans information de quantité/unité
            if quantity is None or quantity_unit is None:
                logger.debug(f"Skipping price without quantity/unit: {item.get('id')}")
                return None

            # Ignorer les prix sans nom de produit
            product_name = product.get("product_name") or product.get("name")
            if not product_name:
                logger.debug(f"Skipping price without product name: {item.get('id')}")
                return None

            return OpenPrice(
                product_name=product_name,
                product_code=product.get("code"),
                price=float(price),
                currency=item.get("currency", "EUR"),
                quantity=float(quantity),
                unit=quantity_unit,
                store_name=item.get("location", {}).get("name") if isinstance(item.get("location"), dict) else None,
                store_location=item.get("location", {}).get("address") if isinstance(item.get("location"), dict) else None,
                date_collected=item.get("date"),
                source_url=item.get("proof_url"),
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.debug(f"Erreur parsing prix: {e}")
            return None

    def health_check(self) -> bool:
        """Vérifie si l'API est accessible."""
        try:
            response = self.session.get(f"{self.base_url}/status", timeout=10)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
