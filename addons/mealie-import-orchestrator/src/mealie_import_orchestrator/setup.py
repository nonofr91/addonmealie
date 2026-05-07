"""Setup script for automatic fake recipe + Addon cookbook creation in Mealie."""
from __future__ import annotations

import logging
import os
import sys
import time

import requests

logger = logging.getLogger(__name__)

ADDON_TAG_NAME = "addon"
ADDON_COOKBOOK_NAME = "Addon"
ADDON_COOKBOOK_FILTER = 'tags.name CONTAINS ALL ["addon"]'


class SetupError(Exception):
    """Error during setup process."""


class MealieSetup:
    """Handles automatic setup of fake recipe + Addon cookbook in Mealie."""

    def __init__(self, mealie_base_url: str, mealie_api_key: str):
        # Ensure mealie_base_url does not end with /api
        base_url = mealie_base_url.rstrip("/")
        if base_url.endswith("/api"):
            base_url = base_url[:-4]
        self.mealie_base_url = base_url
        self.api_key = mealie_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # Mealie readiness
    # ------------------------------------------------------------------

    def _wait_for_mealie(self, max_retries: int = 10, initial_delay: int = 2) -> bool:
        """Wait for Mealie API to be ready with exponential backoff."""
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    f"{self.mealie_base_url}/api/app/about",
                    headers=self.headers,
                    timeout=5,
                )
                if response.status_code == 200:
                    logger.info("Mealie API ready after %d attempt(s)", attempt + 1)
                    return True
            except Exception as exc:
                logger.warning("Attempt %d/%d: Mealie not ready - %s", attempt + 1, max_retries, exc)

            if attempt < max_retries - 1:
                delay = initial_delay * (2 ** attempt)
                logger.info("Waiting %ds before retry...", delay)
                time.sleep(delay)

        logger.error("Mealie API did not become ready after maximum retries")
        return False

    # ------------------------------------------------------------------
    # Tag management
    # ------------------------------------------------------------------

    def _ensure_addon_tag(self) -> str | None:
        """Create the 'addon' tag if it doesn't exist. Returns tag id."""
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
                    logger.debug("Tag '%s' already exists (id=%s)", ADDON_TAG_NAME, tag["id"])
                    return tag["id"]

            resp = requests.post(
                f"{self.mealie_base_url}/api/organizers/tags",
                headers=self.headers,
                json={"name": ADDON_TAG_NAME},
                timeout=10,
            )
            resp.raise_for_status()
            tag_id = resp.json().get("id", "")
            logger.info("Created tag '%s' (id=%s)", ADDON_TAG_NAME, tag_id)
            return tag_id
        except Exception as exc:
            logger.warning("Failed to ensure addon tag: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Cookbook management
    # ------------------------------------------------------------------

    def _ensure_addon_cookbook(self) -> str | None:
        """Create the 'Addon' cookbook if it doesn't exist. Returns cookbook id."""
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
                    logger.debug("Cookbook '%s' already exists", ADDON_COOKBOOK_NAME)
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
            cb_id = resp.json().get("id", "")
            logger.info("Created cookbook '%s' (id=%s)", ADDON_COOKBOOK_NAME, cb_id)
            return cb_id
        except Exception as exc:
            logger.warning("Failed to ensure addon cookbook: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Fake recipe
    # ------------------------------------------------------------------

    def _check_fake_recipe_exists(self, recipe_name: str) -> bool:
        """Check if a fake recipe already exists by name."""
        try:
            response = requests.get(
                f"{self.mealie_base_url}/api/recipes",
                headers=self.headers,
                params={"search": recipe_name, "perPage": 5},
                timeout=10,
            )
            response.raise_for_status()
            for item in response.json().get("items", []):
                if item.get("name") == recipe_name:
                    return True
            return False
        except Exception as exc:
            logger.warning("Failed to check if fake recipe exists: %s", exc)
            return False

    def _create_fake_recipe(self) -> str:
        """Create the import addon fake recipe in Mealie."""
        ui_url = os.environ.get("ADDON_UI_URL", "")
        recipe_name = "\U0001f4e5 Import de recettes"

        description = (
            "Accès à l'interface de l'addon Import.\n\n"
        )
        if ui_url:
            description += f"➡️ Ouvrir l'UI : {ui_url}"

        fake_recipe_data = {
            "name": recipe_name,
            "description": description,
            "orgURL": ui_url or os.environ.get("ADDON_API_URL", ""),
            "tags": [{"name": ADDON_TAG_NAME}, {"name": "import"}],
        }

        try:
            response = requests.post(
                f"{self.mealie_base_url}/api/recipes",
                headers=self.headers,
                json={"name": recipe_name},
                timeout=10,
            )
            response.raise_for_status()
            slug = response.text.strip('"')

            response = requests.patch(
                f"{self.mealie_base_url}/api/recipes/{slug}",
                headers=self.headers,
                json=fake_recipe_data,
                timeout=10,
            )
            response.raise_for_status()

            response = requests.patch(
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
            )
            response.raise_for_status()

            logger.info("Created fake recipe: %s", slug)
            return slug
        except Exception as exc:
            raise SetupError(f"Failed to create fake recipe: {exc}") from exc

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def setup(self, force: bool = False) -> dict[str, str]:
        """Full setup: tag + cookbook + fake recipe."""
        if not self._wait_for_mealie():
            logger.error("Mealie API not ready, skipping setup")
            return {"status": "failed", "error": "Mealie API not ready"}

        self._ensure_addon_tag()
        self._ensure_addon_cookbook()

        recipe_name = "\U0001f4e5 Import de recettes"
        if not force and self._check_fake_recipe_exists(recipe_name):
            logger.info("Fake recipe already exists, skipping creation")
            return {"status": "skipped", "reason": "already_exists"}

        try:
            slug = self._create_fake_recipe()
            return {"status": "created", "slug": slug}
        except SetupError as exc:
            logger.error("Failed to setup fake recipe: %s", exc)
            return {"status": "failed", "error": str(exc)}

    # Keep backward-compat alias
    setup_fake_recipe = setup


def main():
    """Main entry point for setup script."""
    mealie_base_url = os.environ.get("MEALIE_BASE_URL")
    mealie_api_key = os.environ.get("MEALIE_API_KEY")

    if not mealie_base_url or not mealie_api_key:
        logger.error("MEALIE_BASE_URL or MEALIE_API_KEY not set")
        sys.exit(1)

    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    setup = MealieSetup(mealie_base_url, mealie_api_key)
    result = setup.setup()

    if result["status"] == "created":
        print(f"\u2705 Fake recipe created: {result['slug']}")
    elif result["status"] == "skipped":
        print("\u2139\ufe0f  Fake recipe already exists")
    else:
        print(f"\u274c Failed to create fake recipe: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
