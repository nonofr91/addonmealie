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

    def get_recipe_count(self) -> int:
        """Retourne le nombre total de recettes via les métadonnées de pagination."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/recipes",
                params={"page": 1, "perPage": 1},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("total", 0)
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur comptage recettes: {e}")
            return 0

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

    def get_food(self, food_id: str) -> Optional[dict]:
        """Récupère un food par son ID."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/foods/{food_id}",
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur récupération food {food_id}: {e}")
            return None

    def update_food(self, food_id: str, food_data: dict) -> bool:
        """Met à jour un food via PUT (Mealie v3.15+)."""
        try:
            response = self.session.put(
                f"{self.base_url}/api/foods/{food_id}",
                json=food_data,
                timeout=30,
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur mise à jour food {food_id}: {e}")
            return False

    def get_recipe_extras(self, slug: str) -> dict[str, str]:
        """Récupère le dictionnaire ``extras`` d'une recette (ou ``{}`` si absent)."""
        recipe = self.get_recipe(slug)
        if not recipe:
            return {}
        extras = recipe.get("extras") or {}
        if not isinstance(extras, dict):
            return {}
        return {str(k): str(v) for k, v in extras.items() if v is not None}

    def patch_recipe_notes(self, slug: str, cost_note: str) -> bool:
        """Ajoute ou met à jour la section coût dans les notes de la recette.

        Insère un bloc ``<!-- BUDGET-ADDON -->`` dans les notes existantes.
        Si le bloc existe déjà, il est remplacé.
        """
        recipe = self.get_recipe(slug)
        if not recipe:
            return False

        existing_notes = recipe.get("notes", []) or []

        # Chercher et remplacer un bloc existant
        marker = "💰 Coût estimé"
        found = False
        for i, note_obj in enumerate(existing_notes):
            text = note_obj.get("text", "") if isinstance(note_obj, dict) else str(note_obj)
            if marker in text:
                existing_notes[i] = {"title": "", "text": cost_note}
                found = True
                break

        if not found:
            existing_notes.append({"title": "", "text": cost_note})

        try:
            response = self.session.patch(
                f"{self.base_url}/api/recipes/{slug}",
                json={"notes": existing_notes},
                timeout=30,
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.warning("Patch notes échoué pour '%s': %s", slug, e)
            return False

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

    def patch_cost_data(
        self, slug: str, extras: dict[str, str], cost_note: str
    ) -> bool:
        """Publie extras ET notes de coût sur la recette."""
        recipe = self.get_recipe(slug)
        if not recipe:
            return False

        # Préparer extras
        extras_payload = {
            str(k): str(v) for k, v in extras.items() if v is not None
        }

        # Préparer notes
        existing_notes: list = recipe.get("notes") or []
        marker = "💰 Coût estimé"
        found = False
        for i, note_obj in enumerate(existing_notes):
            text = note_obj.get("text", "") if isinstance(note_obj, dict) else str(note_obj)
            if marker in text:
                existing_notes[i] = {"title": "", "text": cost_note}
                found = True
                break
        if not found:
            existing_notes.append({"title": "", "text": cost_note})

        try:
            recipe["extras"] = extras_payload
            recipe["notes"] = existing_notes
            response = self.session.put(
                f"{self.base_url}/api/recipes/{slug}",
                json=recipe,
                timeout=30,
            )
            response.raise_for_status()
            logger.info("Coûts publiés pour '%s'", slug)
            return True
        except requests.exceptions.RequestException as e:
            logger.warning("Patch coûts échoué pour '%s': %s", slug, e)
            return False
