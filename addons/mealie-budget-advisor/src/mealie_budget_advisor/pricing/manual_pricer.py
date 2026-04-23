"""Gestion de la base de prix manuelle."""

import json
import logging
from pathlib import Path
from typing import Optional

from ..models.pricing import ManualPrice

logger = logging.getLogger(__name__)


class ManualPricer:
    """Gère la base de données de prix manuels."""

    DEFAULT_DATA_PATH = Path(__file__).parent.parent.parent.parent / "data" / "ingredient_prices.json"

    def __init__(self, data_path: Optional[Path] = None) -> None:
        self.data_path = data_path or self.DEFAULT_DATA_PATH
        self._prices: dict[str, ManualPrice] = {}
        self._ensure_file_exists()
        self._load()

    def _ensure_file_exists(self) -> None:
        """Crée le fichier JSON s'il n'existe pas."""
        if not self.data_path.exists():
            self.data_path.parent.mkdir(parents=True, exist_ok=True)
            self._save()

    def _load(self) -> None:
        """Charge les prix depuis le fichier JSON."""
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._prices = {}
            for name, item in data.items():
                try:
                    self._prices[name.lower()] = ManualPrice(**item)
                except Exception as e:
                    logger.warning(f"Erreur chargement prix pour {name}: {e}")

            logger.info(f"{len(self._prices)} prix manuels chargés")
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Fichier prix vide ou corrompu: {e}")
            self._prices = {}

    def _save(self) -> None:
        """Sauvegarde les prix dans le fichier JSON."""
        data = {
            name: price.model_dump() for name, price in self._prices.items()
        }
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)

    def get_price(self, ingredient_name: str) -> Optional[ManualPrice]:
        """Récupère le prix d'un ingrédient.

        Args:
            ingredient_name: Nom de l'ingrédient (normalisé)

        Returns:
            Prix manuel ou None
        """
        normalized = ingredient_name.lower().strip()
        return self._prices.get(normalized)

    def set_price(
        self,
        ingredient_name: str,
        price_per_unit: float,
        unit: str,
        store: Optional[str] = None,
        location: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> ManualPrice:
        """Définit ou met à jour le prix d'un ingrédient.

        Args:
            ingredient_name: Nom de l'ingrédient
            price_per_unit: Prix par unité de base
            unit: Unité (kg, g, l, ml, unit)
            store: Magasin (optionnel)
            location: Localisation (optionnel)
            notes: Notes (optionnel)

        Returns:
            Prix créé/mis à jour
        """
        normalized = ingredient_name.lower().strip()

        price = ManualPrice(
            ingredient_name=ingredient_name,
            price_per_unit=price_per_unit,
            unit=unit,
            store=store,
            location=location,
            notes=notes,
        )

        self._prices[normalized] = price
        self._save()

        logger.info(f"Prix défini pour {ingredient_name}: {price_per_unit}€/{unit}")
        return price

    def delete_price(self, ingredient_name: str) -> bool:
        """Supprime le prix d'un ingrédient.

        Args:
            ingredient_name: Nom de l'ingrédient

        Returns:
            True si supprimé, False si inexistant
        """
        normalized = ingredient_name.lower().strip()
        if normalized in self._prices:
            del self._prices[normalized]
            self._save()
            logger.info(f"Prix supprimé pour {ingredient_name}")
            return True
        return False

    def list_prices(self, search: Optional[str] = None) -> list[ManualPrice]:
        """Liste tous les prix, avec filtre optionnel.

        Args:
            search: Terme de recherche (optionnel)

        Returns:
            Liste des prix
        """
        prices = list(self._prices.values())

        if search:
            search_lower = search.lower()
            prices = [p for p in prices if search_lower in p.ingredient_name.lower()]

        return sorted(prices, key=lambda p: p.ingredient_name)

    def get_coverage_stats(self) -> dict:
        """Retourne des statistiques sur la couverture."""
        return {
            "total_ingredients": len(self._prices),
            "with_store_info": sum(1 for p in self._prices.values() if p.store),
            "with_location": sum(1 for p in self._prices.values() if p.location),
        }
