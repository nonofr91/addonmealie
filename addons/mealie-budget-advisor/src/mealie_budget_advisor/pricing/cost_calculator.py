"""Calculateur de coût pour les recettes Mealie."""

import logging
from typing import Optional

import requests

from ..mealie_sync import MealieClient
from ..models.cost import CostBreakdown, IngredientCost, RecipeCost
from ..recipe_extras import build_addon_extras, merge_extras, read_override
from .ingredient_matcher import IngredientMatcher
from .manual_pricer import ManualPricer
from .open_prices_client import OpenPricesClient

logger = logging.getLogger(__name__)


class CostCalculator:
    """Calcule le coût des recettes en combinant toutes les sources de prix."""

    def __init__(
        self,
        mealie_base_url: Optional[str] = None,
        mealie_api_key: Optional[str] = None,
        ingredient_matcher: Optional[IngredientMatcher] = None,
    ) -> None:
        self.mealie_base_url = (mealie_base_url or "http://localhost:9925").rstrip("/")
        self.mealie_api_key = mealie_api_key or ""

        # Initialiser le matcher avec ses dépendances
        if ingredient_matcher:
            self.matcher = ingredient_matcher
        else:
            manual = ManualPricer()
            open_prices = OpenPricesClient()
            self.matcher = IngredientMatcher(manual, open_prices)

        self._session = requests.Session()
        self._session.headers.update({
            "Accept": "application/json",
            "Authorization": f"Bearer {self.mealie_api_key}" if self.mealie_api_key else "",
        })

    def get_recipe(self, slug: str) -> Optional[dict]:
        """Récupère une recette depuis Mealie."""
        try:
            response = self._session.get(
                f"{self.mealie_base_url}/api/recipes/{slug}",
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur récupération recette {slug}: {e}")
            return None

    def calculate_cost(
        self,
        recipe_slug: str,
        use_open_prices: bool = True,
    ) -> Optional[RecipeCost]:
        """Calcule le coût d'une recette.

        Args:
            recipe_slug: Slug de la recette dans Mealie
            use_open_prices: Utiliser Open Prices comme fallback

        Returns:
            RecipeCost ou None si erreur
        """
        recipe = self.get_recipe(recipe_slug)
        if not recipe:
            return None

        recipe_name = recipe.get("name", recipe_slug)
        servings = self._extract_servings(recipe)

        # Extraire les ingrédients
        ingredients = recipe.get("recipeIngredient", [])
        if not ingredients:
            logger.warning(f"Recette {recipe_slug} sans ingrédients")

        breakdown = CostBreakdown(ingredients=[])
        total_confidence = 0.0

        for ing_data in ingredients:
            note = self._extract_note(ing_data)
            if not note:
                continue

            # Parser la note
            quantity, unit, name = self.matcher.parse_ingredient_note(note)

            # Trouver le prix
            price, source, confidence = self.matcher.find_price(
                name, quantity, unit, use_open_prices
            )

            total_confidence += confidence

            ing_cost = IngredientCost(
                ingredient_name=name,
                original_note=note,
                quantity=quantity,
                unit=unit,
                price_per_unit=self._calculate_price_per_unit(price, quantity),
                total_cost=price,
                price_source=source,
                confidence=confidence,
            )
            breakdown.ingredients.append(ing_cost)

        # Calculer la confiance moyenne
        if breakdown.ingredients:
            avg_confidence = total_confidence / len(breakdown.ingredients)
        else:
            avg_confidence = 0.0

        # Lecture d'un éventuel override manuel depuis extras.cout_manuel_*
        override = read_override(recipe.get("extras"))

        return RecipeCost(
            recipe_slug=recipe_slug,
            recipe_name=recipe_name,
            servings=servings,
            breakdown=breakdown,
            override_per_serving=override.per_serving,
            override_total=override.total,
            override_reason=override.reason,
        )

    def calculate_batch_costs(
        self,
        slugs: list[str],
        use_open_prices: bool = True,
    ) -> list[RecipeCost]:
        """Calcule les coûts pour plusieurs recettes.

        Args:
            slugs: Liste des slugs de recettes
            use_open_prices: Utiliser Open Prices

        Returns:
            Liste des RecipeCost (erreurs ignorées)
        """
        results = []
        for slug in slugs:
            cost = self.calculate_cost(slug, use_open_prices)
            if cost:
                results.append(cost)
        return results

    def _extract_servings(self, recipe: dict) -> int:
        """Extrait le nombre de portions d'une recette."""
        servings_raw = recipe.get("recipeServings") or recipe.get("recipeYield") or "1"
        try:
            # Peut être "4 portions" ou juste "4"
            import re
            numbers = re.findall(r'\d+', str(servings_raw))
            if numbers:
                return max(1, int(numbers[0]))
        except (ValueError, TypeError):
            pass
        return 1

    def _extract_note(self, ingredient_data: dict) -> str:
        """Extrait le texte d'un ingrédient.

        Préfère ``originalText`` car Mealie peut perdre l'unité lors du
        parsing (ex. ``25 cl de vin blanc`` → display ``25 vin blanc``).
        """
        # originalText conserve le texte saisi (avec unités intactes)
        note = ingredient_data.get("originalText", "")
        if not note:
            note = ingredient_data.get("note", "")
        if not note:
            note = ingredient_data.get("display", "")
        if not note and ingredient_data.get("food"):
            # Construire depuis l'objet food + quantité
            food = ingredient_data.get("food", {})
            food_name = food.get("name", "")
            quantity = ingredient_data.get("quantity", "")
            unit = ingredient_data.get("unit", {}).get("name", "")
            if food_name:
                note = f"{quantity} {unit} {food_name}".strip()
        return note

    def _calculate_price_per_unit(self, total_price: float, quantity: float) -> float:
        """Calcule le prix par unité."""
        if quantity == 0:
            return 0.0
        return round(total_price / quantity, 4)

    def sync_recipe_cost(
        self,
        slug: str,
        month: Optional[str] = None,
        use_open_prices: bool = True,
        mealie_client: Optional["MealieClient"] = None,
    ) -> dict:
        """Recalcule le coût d'une recette et le publie dans ``extras`` de Mealie.

        Les clés utilisateur (``cout_manuel_*``) ne sont JAMAIS écrasées.

        Args:
            slug: Slug de la recette.
            month: Mois de référence (``YYYY-MM``). Si ``None``, mois courant.
            use_open_prices: Utiliser Open Prices comme fallback.
            mealie_client: Client Mealie injectable (sinon créé depuis la config
                du calculateur).

        Returns:
            ``dict`` avec :
                - ``success`` (bool)
                - ``slug`` (str)
                - ``patched`` (bool) : PATCH Mealie réussi
                - ``has_override`` (bool) : override manuel détecté sur la recette
                - ``extras`` (dict[str, str]) : extras complets envoyés à Mealie
                - ``cost`` (dict) : RecipeCost sérialisé
                - ``error`` (str, optionnel)
        """
        client = mealie_client or MealieClient(
            self.mealie_base_url, self.mealie_api_key
        )

        recipe = self.get_recipe(slug)
        if not recipe:
            return {
                "success": False,
                "slug": slug,
                "patched": False,
                "has_override": False,
                "error": f"Recette {slug} introuvable",
            }

        cost = self.calculate_cost(slug, use_open_prices=use_open_prices)
        if not cost:
            return {
                "success": False,
                "slug": slug,
                "patched": False,
                "has_override": False,
                "error": f"Calcul de coût impossible pour {slug}",
            }

        source = "manuel" if cost.has_override else "auto"
        addon_extras = build_addon_extras(cost, month=month, source=source)
        merged = merge_extras(recipe.get("extras") or {}, addon_extras)
        patched = client.patch_extras(slug, merged)

        # Écrire le coût dans les notes de la recette (visible dans Mealie UI)
        cost_note = (
            f"💰 Coût estimé : {cost.cost_per_serving:.2f} €/portion"
            f" ({cost.total_cost:.2f} € total pour {cost.servings} portions)"
        )
        client.patch_recipe_notes(slug, cost_note)

        return {
            "success": patched,
            "slug": slug,
            "patched": patched,
            "has_override": cost.has_override,
            "extras": merged,
            "cost": cost.model_dump(),
        }

    def refresh_all_costs(
        self,
        month: Optional[str] = None,
        use_open_prices: bool = True,
        mealie_client: Optional["MealieClient"] = None,
        limit: int = 1000,
    ) -> dict:
        """Recalcule et publie les coûts pour toutes les recettes Mealie.

        Ne touche jamais aux ``extras.cout_manuel_*`` existants.

        Returns:
            Dictionnaire récapitulatif :
                - ``total`` : nombre de recettes examinées
                - ``updated`` : PATCH réussis
                - ``failed`` : PATCH échoués
                - ``skipped`` : recettes sans ingrédients
                - ``overrides_preserved`` : recettes avec override utilisateur
                - ``month`` : mois de référence utilisé
        """
        client = mealie_client or MealieClient(
            self.mealie_base_url, self.mealie_api_key
        )

        recipes = client.get_all_recipes(limit=limit)
        summary = {
            "total": len(recipes),
            "updated": 0,
            "failed": 0,
            "skipped": 0,
            "overrides_preserved": 0,
            "month": month or "",
        }

        for recipe in recipes:
            slug = recipe.get("slug")
            if not slug:
                summary["skipped"] += 1
                continue
            result = self.sync_recipe_cost(
                slug=slug,
                month=month,
                use_open_prices=use_open_prices,
                mealie_client=client,
            )
            if not result.get("success"):
                summary["failed"] += 1
                continue
            summary["updated"] += 1
            if result.get("has_override"):
                summary["overrides_preserved"] += 1

        return summary

    def compare_recipes_by_cost(
        self,
        slugs: list[str],
        per_serving: bool = True,
    ) -> list[tuple[str, float]]:
        """Compare plusieurs recettes par coût.

        Args:
            slugs: Liste des slugs
            per_serving: Comparer par portion (vs total)

        Returns:
            Liste triée (slug, coût)
        """
        costs = []
        for slug in slugs:
            cost = self.calculate_cost(slug)
            if cost:
                price = cost.cost_per_serving if per_serving else cost.total_cost
                costs.append((slug, price))

        return sorted(costs, key=lambda x: x[1])
