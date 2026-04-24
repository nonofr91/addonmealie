"""Synchronisation avec l'API Mealie."""

import logging
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)


class MealieClient:
    """Client pour interagir avec l'API Mealie."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        self.base_url = (base_url or "http://localhost:9925").rstrip("/")
        self.api_key = api_key or ""

        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        if self.api_key:
            self.session.headers["Authorization"] = f"Bearer {self.api_key}"

    def health_check(self) -> dict[str, Any]:
        """Vérifie la connexion à Mealie."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/app/about",
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            return {
                "connected": True,
                "version": data.get("version", "unknown"),
                "demo": data.get("demo", False),
            }
        except requests.exceptions.RequestException as e:
            return {
                "connected": False,
                "error": str(e),
            }

    def get_all_recipes(self, limit: int = 1000) -> list[dict]:
        """Récupère toutes les recettes."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/recipes",
                params={"page": 1, "perPage": limit, "orderBy": "name", "orderDirection": "asc"},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("items", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur récupération recettes: {e}")
            return []

    def get_recipe(self, slug: str) -> Optional[dict]:
        """Récupère une recette par son slug."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/recipes/{slug}",
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur récupération recette {slug}: {e}")
            return None

    def get_foods(self) -> list[dict]:
        """Récupère tous les aliments (foods)."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/foods",
                params={"page": 1, "perPage": 10000},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("items", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur récupération foods: {e}")
            return []

    def get_units(self) -> list[dict]:
        """Récupère toutes les unités."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/units",
                params={"page": 1, "perPage": 1000},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("items", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur récupération units: {e}")
            return []

    def get_recipe_extras(self, slug: str) -> dict[str, str]:
        """Récupère le dictionnaire ``extras`` d'une recette (ou ``{}`` si absent)."""
        recipe = self.get_recipe(slug)
        if not recipe:
            return {}
        extras = recipe.get("extras") or {}
        if not isinstance(extras, dict):
            return {}
        return {str(k): str(v) for k, v in extras.items() if v is not None}

    def patch_extras(self, slug: str, extras: dict[str, str]) -> bool:
        """Patch le champ ``extras`` d'une recette.

        Mealie n'accepte que des valeurs strings dans ``extras``. Toute valeur
        non-string est sérialisée via ``str()``.

        Args:
            slug: Slug de la recette.
            extras: Dictionnaire complet à écrire (Mealie remplace l'ensemble).

        Returns:
            ``True`` si le PATCH a réussi, ``False`` sinon.
        """
        try:
            payload = {str(k): str(v) for k, v in extras.items() if v is not None}
            response = self.session.patch(
                f"{self.base_url}/api/recipes/{slug}",
                json={"extras": payload},
                timeout=30,
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.warning("Patch extras échoué pour '%s': %s", slug, e)
            return False
