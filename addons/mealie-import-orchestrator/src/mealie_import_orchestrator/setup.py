"""Setup script for automatic fake recipe creation in Mealie."""
from __future__ import annotations

import logging
import os
import sys

import requests

logger = logging.getLogger(__name__)


class SetupError(Exception):
    """Error during setup process."""


class MealieSetup:
    """Handles automatic setup of fake recipe in Mealie."""

    def __init__(self, mealie_base_url: str, mealie_api_key: str):
        self.mealie_base_url = mealie_base_url.rstrip("/")
        self.api_key = mealie_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _check_fake_recipe_exists(self) -> bool:
        """Check if the fake recipe already exists."""
        try:
            response = requests.get(
                f"{self.mealie_base_url}/api/recipes",
                headers=self.headers,
                params={"search": "📥 Import de recettes"},
            )
            response.raise_for_status()
            data = response.json()
            return len(data.get("items", [])) > 0
        except Exception as exc:
            logger.warning(f"Failed to check if fake recipe exists: {exc}")
            return False

    def _create_fake_recipe(self) -> str:
        """Create the fake recipe in Mealie."""
        fake_recipe_data = {
            "name": "📥 Import de recettes",
            "description": "Recette spéciale pour accéder à l'interface de l'addon Mealie Import. Cette recette sert de point d'entrée vers l'UI de l'addon.",
            "recipeYield": "1 serving",
            "orgURL": f"{os.environ.get('ADDON_API_URL', 'http://localhost:8000')}",
            "tags": [{"name": "addon"}, {"name": "import"}],
            "categories": [{"name": "Tools"}],
        }

        try:
            # Create recipe
            response = requests.post(
                f"{self.mealie_base_url}/api/recipes",
                headers=self.headers,
                json={"name": fake_recipe_data["name"]},
            )
            response.raise_for_status()
            slug = response.text.strip('"')

            # Update with full data
            response = requests.patch(
                f"{self.mealie_base_url}/api/recipes/{slug}",
                headers=self.headers,
                json=fake_recipe_data,
            )
            response.raise_for_status()

            logger.info(f"Created fake recipe: {slug}")
            return slug

        except Exception as exc:
            raise SetupError(f"Failed to create fake recipe: {exc}") from exc

    def setup_fake_recipe(self, force: bool = False) -> dict[str, str]:
        """Setup fake recipe if it doesn't exist."""
        if not force and self._check_fake_recipe_exists():
            logger.info("Fake recipe already exists, skipping creation")
            return {"status": "skipped", "reason": "already_exists"}

        try:
            slug = self._create_fake_recipe()
            return {"status": "created", "slug": slug}
        except SetupError as exc:
            logger.error(f"Failed to setup fake recipe: {exc}")
            return {"status": "failed", "error": str(exc)}


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
    result = setup.setup_fake_recipe()

    if result["status"] == "created":
        print(f"✅ Fake recipe created: {result['slug']}")
    elif result["status"] == "skipped":
        print("ℹ️  Fake recipe already exists")
    else:
        print(f"❌ Failed to create fake recipe: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
