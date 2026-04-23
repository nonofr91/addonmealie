"""Compute per-recipe cost from parsed ingredients + matched prices."""

from __future__ import annotations

import logging
from typing import Optional

from ..models.cost import IngredientCost, RecipeCost
from ..models.pricing import PriceSource
from .ingredient_matcher import IngredientMatcher, MatchedPrice
from .ingredient_parser import ParsedIngredient, parse_ingredient

logger = logging.getLogger(__name__)


class CostCalculator:
    """Translate Mealie ingredient lines into a `RecipeCost`."""

    def __init__(self, matcher: IngredientMatcher) -> None:
        self.matcher = matcher

    def cost_of_line(self, text: str) -> IngredientCost:
        parsed = parse_ingredient(text)
        matched = self.matcher.match(parsed.food_name, parsed.unit) if parsed.food_name else None
        return self._build(parsed, matched, original=text)

    def cost_of_recipe(
        self,
        recipe_slug: str,
        recipe_name: str,
        ingredient_texts: list[str],
        servings: int = 1,
        currency: str = "EUR",
    ) -> RecipeCost:
        breakdown: list[IngredientCost] = []
        resolved = 0
        for text in ingredient_texts:
            line = self.cost_of_line(text)
            breakdown.append(line)
            if line.price_source != PriceSource.estimated or line.total_cost > 0:
                if line.total_cost > 0:
                    resolved += 1

        total_cost = round(sum(line.total_cost for line in breakdown), 2)
        servings = max(servings, 1)
        confidence = resolved / len(breakdown) if breakdown else 0.0
        return RecipeCost(
            recipe_slug=recipe_slug,
            recipe_name=recipe_name,
            servings=servings,
            total_cost=total_cost,
            cost_per_serving=round(total_cost / servings, 2),
            currency=currency,
            ingredient_breakdown=breakdown,
            confidence=round(confidence, 3),
        )

    @staticmethod
    def _build(parsed: ParsedIngredient, matched: Optional[MatchedPrice], original: str) -> IngredientCost:
        if matched is None:
            return IngredientCost(
                ingredient_name=parsed.food_name or original,
                original_note=original,
                quantity=parsed.quantity,
                unit=parsed.unit,
                price_per_unit=0.0,
                total_cost=0.0,
                price_source=PriceSource.estimated,
            )
        return IngredientCost(
            ingredient_name=parsed.food_name or original,
            original_note=original,
            quantity=parsed.quantity,
            unit=parsed.unit,
            price_per_unit=round(matched.price_per_unit_base, 6),
            total_cost=round(parsed.quantity * matched.price_per_unit_base, 2),
            price_source=matched.source,
        )
