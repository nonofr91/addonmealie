"""Setup script for automatic Nutrition Advisor fake recipe in Mealie."""
from __future__ import annotations

import logging
import os
import time

import requests

logger = logging.getLogger(__name__)

ADDON_TAG_NAME = "addon"
ADDON_COOKBOOK_NAME = "Addon"
ADDON_COOKBOOK_FILTER = 'tags.name CONTAINS ALL ["addon"]'


class MealieSetup:
    """Creates the Nutrition Advisor placeholder recipe + Addon cookbook."""

    def __init__(self, mealie_base_url: str, mealie_api_key: str):
        # Ensure mealie_base_url does not end with /api
        base_url = mealie_base_url.rstrip("/")
        if base_url.endswith("/api"):
            base_url = base_url[:-4]
        self.mealie_base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {mealie_api_key}",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # Mealie readiness
    # ------------------------------------------------------------------

    def _wait_for_mealie(self, max_retries: int = 10, initial_delay: int = 2) -> bool:
        for attempt in range(max_retries):
            try:
                resp = requests.get(
                    f"{self.mealie_base_url}/api/app/about",
                    headers=self.headers,
                    timeout=5,
                )
                if resp.status_code == 200:
                    logger.info("Mealie API ready after %d attempt(s)", attempt + 1)
                    return True
            except Exception as exc:
                logger.warning("Attempt %d/%d: Mealie not ready - %s", attempt + 1, max_retries, exc)
            if attempt < max_retries - 1:
                delay = initial_delay * (2 ** attempt)
                time.sleep(delay)
        logger.error("Mealie API did not become ready")
        return False

    # ------------------------------------------------------------------
    # Tag + cookbook (idempotent)
    # ------------------------------------------------------------------

    def _ensure_addon_tag(self) -> str | None:
        try:
            resp = requests.get(
                f"{self.mealie_base_url}/api/organizers/tags",
                headers=self.headers,
                params={"page": 1, "perPage": 100},
                timeout=10,
            )
            resp.raise_for_status()
            for tag in resp.json().get("items", []):
                if tag.get("name") == ADDON_TAG_NAME:
                    return tag["id"]
            resp = requests.post(
                f"{self.mealie_base_url}/api/organizers/tags",
                headers=self.headers,
                json={"name": ADDON_TAG_NAME},
                timeout=10,
            )
            resp.raise_for_status()
            tag_id = resp.json().get("id", "")
            logger.info("Created tag '%s'", ADDON_TAG_NAME)
            return tag_id
        except Exception as exc:
            logger.warning("Failed to ensure addon tag: %s", exc)
            return None

    def _ensure_addon_cookbook(self) -> str | None:
        try:
            resp = requests.get(
                f"{self.mealie_base_url}/api/households/cookbooks",
                headers=self.headers,
                params={"page": 1, "perPage": 100},
                timeout=10,
            )
            resp.raise_for_status()
            for cb in resp.json().get("items", []):
                if cb.get("name") == ADDON_COOKBOOK_NAME:
                    return cb.get("id")
            resp = requests.post(
                f"{self.mealie_base_url}/api/households/cookbooks",
                headers=self.headers,
                json={
                    "name": ADDON_COOKBOOK_NAME,
                    "description": "Recettes-liens vers les interfaces des addons Mealie.",
                    "public": True,
                    "queryFilterString": ADDON_COOKBOOK_FILTER,
                },
                timeout=10,
            )
            resp.raise_for_status()
            logger.info("Created cookbook '%s'", ADDON_COOKBOOK_NAME)
            return resp.json().get("id")
        except Exception as exc:
            logger.warning("Failed to ensure addon cookbook: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Fake recipe
    # ------------------------------------------------------------------

    def _recipe_exists(self, recipe_name: str) -> bool:
        try:
            resp = requests.get(
                f"{self.mealie_base_url}/api/recipes",
                headers=self.headers,
                params={"search": recipe_name, "perPage": 5},
                timeout=10,
            )
            resp.raise_for_status()
            return any(r.get("name") == recipe_name for r in resp.json().get("items", []))
        except Exception:
            return False

    def _create_fake_recipe(self) -> str:
        ui_url = os.environ.get("ADDON_UI_URL", "")
        recipe_name = "\U0001f957 Nutrition Advisor"

        description = "Acc\u00e8s \u00e0 l'interface de l'addon Nutrition.\n\n"
        if ui_url:
            description += f"\u27a1\ufe0f Ouvrir l'UI : {ui_url}"

        resp = requests.post(
            f"{self.mealie_base_url}/api/recipes",
            headers=self.headers,
            json={"name": recipe_name},
            timeout=10,
        )
        resp.raise_for_status()
        slug = resp.text.strip('"')

        requests.patch(
            f"{self.mealie_base_url}/api/recipes/{slug}",
            headers=self.headers,
            json={
                "name": recipe_name,
                "description": description,
                "orgURL": ui_url,
                "tags": [{"name": ADDON_TAG_NAME}, {"name": "nutrition"}],
            },
            timeout=10,
        ).raise_for_status()

        requests.patch(
            f"{self.mealie_base_url}/api/recipes/{slug}",
            headers=self.headers,
            json={
                "recipeServings": 0,
                "totalTime": None,
                "prepTime": None,
                "cookTime": None,
                "performTime": None,
                "recipeYield": None,
                "recipeYieldQuantity": None,
            },
            timeout=10,
        ).raise_for_status()

        logger.info("Created fake recipe: %s", slug)
        return slug

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def setup(self) -> dict[str, str]:
        if not self._wait_for_mealie():
            return {"status": "failed", "error": "Mealie API not ready"}

        self._ensure_addon_tag()
        self._ensure_addon_cookbook()

        recipe_name = "\U0001f957 Nutrition Advisor"
        if self._recipe_exists(recipe_name):
            logger.info("Fake recipe '%s' already exists", recipe_name)
            return {"status": "skipped"}

        try:
            slug = self._create_fake_recipe()
            return {"status": "created", "slug": slug}
        except Exception as exc:
            logger.error("Failed to create fake recipe: %s", exc)
            return {"status": "failed", "error": str(exc)}
