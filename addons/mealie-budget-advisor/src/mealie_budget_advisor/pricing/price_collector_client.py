"""Client pour l'addon ingredient-price-collector."""

import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class PriceCollectorClient:
    """Client HTTP vers l'addon ingredient-price-collector."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})

    def search_price(
        self,
        ingredient: str,
        unit: Optional[str] = None,
    ) -> Optional[tuple[float, str]]:
        """Cherche un prix pour un ingrédient.

        Args:
            ingredient: Nom de l'ingrédient
            unit: Unité souhaitée (kg, l, piece, unit) — optionnel

        Returns:
            Tuple (prix, unité) ou None si non trouvé
        """
        try:
            params: dict = {"ingredient": ingredient}
            if unit:
                params["unit"] = unit

            response = self._session.get(
                f"{self.base_url}/prices/search",
                params=params,
                timeout=5,
            )
            response.raise_for_status()
            data = response.json()

            price = data.get("recommended_price")
            rec_unit = data.get("recommended_unit")
            warnings = data.get("warnings", [])

            if price is None or "price_unknown" in warnings:
                logger.debug(f"Price collector: aucun prix pour '{ingredient}'")
                return None

            logger.debug(
                f"Price collector: {ingredient} → {price} €/{rec_unit} "
                f"(confiance {data.get('confidence', '?')})"
            )
            return float(price), rec_unit or unit or "kg"

        except requests.exceptions.RequestException as e:
            logger.warning(f"Price collector inaccessible pour '{ingredient}': {e}")
            return None

    def health_check(self) -> bool:
        """Vérifie si le service est accessible."""
        try:
            r = self._session.get(f"{self.base_url}/health", timeout=3)
            return r.status_code == 200
        except requests.exceptions.RequestException:
            return False
