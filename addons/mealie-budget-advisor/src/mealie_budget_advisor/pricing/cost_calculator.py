"""Calculateur de coût pour les recettes Mealie."""

import logging
from typing import Optional

import requests

from ..mealie_sync import MealieClient
from ..models.cost import CostBreakdown, IngredientCost, RecipeCost
from ..recipe_extras import build_addon_extras, merge_extras, read_override
from .ingredient_matcher import IngredientMatcher
from .ingredient_weights import get_ingredient_weight
from .manual_pricer import ManualPricer
from .open_prices_client import OpenPricesClient
from .price_collector_client import PriceCollectorClient

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
            price_collector = None
            try:
                from ..config import get_config
                cfg = get_config()
                if cfg.price_collector_url:
                    price_collector = PriceCollectorClient(cfg.price_collector_url)
            except Exception:
                pass
            self.matcher = IngredientMatcher(manual, open_prices, price_collector)

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
                display_quantity=self._format_display_quantity(quantity, unit),
                priced_quantity=self._format_priced_quantity(name, quantity, unit, source),
                pricing_detail=self._format_pricing_detail(name, quantity, unit, price, source),
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

    def _format_display_quantity(self, quantity: float, unit: str) -> str:
        return f"{self._format_number(quantity)} {self._french_unit(unit, quantity)}"

    def _format_priced_quantity(
        self,
        ingredient_name: str,
        quantity: float,
        unit: str,
        source: str,
    ) -> str:
        if source == "free":
            return "gratuit"

        qty_base, unit_base = self.matcher.normalize_quantity(quantity, unit)
        if unit_base == "unit":
            weight_kg = qty_base * get_ingredient_weight(ingredient_name)
            return self._format_weight(weight_kg)
        if unit_base == "ml":
            return self._format_weight(self.matcher._estimate_ml_as_kg(ingredient_name, qty_base))
        if unit_base == "kg":
            return self._format_weight(qty_base)
        if unit_base == "l":
            return self._format_volume_l(qty_base)
        return f"{self._format_number(qty_base)} {self._french_unit(unit_base, qty_base)}"

    def _format_pricing_detail(
        self,
        ingredient_name: str,
        quantity: float,
        unit: str,
        total_price: float,
        source: str,
    ) -> str:
        if source == "free":
            return "Ingrédient considéré comme gratuit"
        priced_quantity = self._format_priced_quantity(ingredient_name, quantity, unit, source)
        if total_price <= 0:
            return f"Quantité valorisée : {priced_quantity}"
        if priced_quantity.endswith("kg"):
            qty = float(priced_quantity.replace(" kg", "").replace(",", "."))
            unit_price = total_price / qty if qty else 0.0
            return f"{priced_quantity} × {self._format_currency(unit_price)}/kg"
        if priced_quantity.endswith("g"):
            qty_g = float(priced_quantity.replace(" g", "").replace(",", "."))
            qty_kg = qty_g / 1000
            unit_price = total_price / qty_kg if qty_kg else 0.0
            return f"{priced_quantity} × {self._format_currency(unit_price)}/kg"
        if priced_quantity.endswith("cl"):
            qty_cl = float(priced_quantity.replace(" cl", "").replace(",", "."))
            qty_l = qty_cl / 100
            unit_price = total_price / qty_l if qty_l else 0.0
            return f"{priced_quantity} × {self._format_currency(unit_price)}/l"
        if priced_quantity.endswith("l"):
            qty_l = float(priced_quantity.replace(" l", "").replace(",", "."))
            unit_price = total_price / qty_l if qty_l else 0.0
            return f"{priced_quantity} × {self._format_currency(unit_price)}/l"
        return f"Quantité valorisée : {priced_quantity}"

    def _format_weight(self, weight_kg: float) -> str:
        if weight_kg < 1:
            return f"{self._format_number(weight_kg * 1000)} g"
        return f"{self._format_number(weight_kg)} kg"

    def _format_volume_l(self, volume_l: float) -> str:
        if volume_l < 1:
            return f"{self._format_number(volume_l * 100)} cl"
        return f"{self._format_number(volume_l)} l"

    def _french_unit(self, unit: str, quantity: float) -> str:
        units = {
            "unit": "pièce" if quantity <= 1 else "pièces",
            "g": "g",
            "kg": "kg",
            "ml": "ml",
            "cl": "cl",
            "l": "l",
            "tsp": "cuillère à café" if quantity <= 1 else "cuillères à café",
            "tbsp": "cuillère à soupe" if quantity <= 1 else "cuillères à soupe",
            "cup": "tasse" if quantity <= 1 else "tasses",
        }
        return units.get(unit, unit)

    def _format_number(self, value: float) -> str:
        rounded = round(value, 2)
        if rounded.is_integer():
            return str(int(rounded))
        return f"{rounded:.2f}".replace(".", ",")

    def _format_currency(self, value: float) -> str:
        return f"{value:.2f} €".replace(".", ",")

    def _format_source_label(self, source: str) -> str:
        labels = {
            "manual": "prix manuel",
            "price_collector": "prix collecté",
            "open_prices": "Open Prices",
            "estimated": "estimation",
            "free": "gratuit",
            "unknown": "inconnu",
        }
        return labels.get(source, source or "inconnu")

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

        # Écrire extras + notes dans un seul PATCH pour éviter les conflits
        cost_note = (
            f"💰 Coût estimé : {self._format_currency(cost.cost_per_serving)}/portion"
            f" ({self._format_currency(cost.total_cost)} total pour {cost.servings} portions)\n\n"
            f"📝 Détail des ingrédients :\n"
        )
        for ing in cost.breakdown.ingredients:
            cost_note += (
                f"- {ing.ingredient_name} : "
                f"{ing.display_quantity or self._format_display_quantity(ing.quantity, ing.unit)}"
                f" → {ing.priced_quantity or 'quantité non valorisée'}"
                f" : {self._format_currency(ing.total_cost)}"
                f" ({self._format_source_label(ing.price_source)})"
            )
            if ing.pricing_detail:
                cost_note += f" — {ing.pricing_detail}"
            cost_note += "\n"
        patched = client.patch_cost_data(slug, merged, cost_note)

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
