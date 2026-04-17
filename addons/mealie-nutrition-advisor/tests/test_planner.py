"""Tests for planner components (AllergyFilter, RecipeScorer)."""

import pytest

from mealie_nutrition_advisor.models.menu import MealType
from mealie_nutrition_advisor.models.profile import (
    ActivityLevel,
    DietaryRestriction,
    Goal,
    HouseholdProfile,
    MemberProfile,
    Sex,
)
from mealie_nutrition_advisor.planner.allergy_filter import AllergyFilter
from mealie_nutrition_advisor.planner.scorer import RecipeScorer


def _member(**kwargs) -> MemberProfile:
    defaults = dict(name="Test", age=30, sex=Sex.female, weight_kg=65, height_cm=168,
                    activity_level=ActivityLevel.moderately_active, goal=Goal.maintenance)
    defaults.update(kwargs)
    return MemberProfile(**defaults)


def _recipe(name: str = "Test Recipe", ingredients: list[str] | None = None, kcal: float = 300) -> dict:
    recipe_ingredients = [{"note": ing} for ing in (ingredients or ["100g poulet", "sel"])]
    return {
        "slug": name.lower().replace(" ", "-"),
        "name": name,
        "recipeIngredient": recipe_ingredients,
        "recipeServings": 4,
        "nutrition": {
            "calories": str(kcal * 4),
            "proteinContent": "100g",
            "fatContent": "40g",
            "carbohydrateContent": "120g",
            "fiberContent": "8g",
            "sodiumContent": "400mg",
        },
    }


class TestAllergyFilter:
    def test_no_restriction(self):
        flt = AllergyFilter()
        member = _member()
        recipe = _recipe()
        safe, reason = flt.is_safe_for_member(recipe, member)
        assert safe is True
        assert reason == ""

    def test_allergen_detected(self):
        flt = AllergyFilter()
        member = _member(allergies=["cacahuètes"])
        recipe = _recipe(ingredients=["100g de cacahuètes grillées"])
        safe, reason = flt.is_safe_for_member(recipe, member)
        assert safe is False
        assert "cacahuètes" in reason

    def test_vegetarian_restriction(self):
        flt = AllergyFilter()
        member = _member(dietary_restrictions=[DietaryRestriction.vegetarian])
        recipe = _recipe(ingredients=["500g de viande hachée", "oignon"])
        safe, reason = flt.is_safe_for_member(recipe, member)
        assert safe is False
        assert "vegetarian" in reason

    def test_gluten_free(self):
        flt = AllergyFilter()
        member = _member(dietary_restrictions=[DietaryRestriction.gluten_free])
        recipe_with_gluten = _recipe(ingredients=["200g de farine de blé"])
        recipe_without = _recipe(ingredients=["300g de riz", "légumes"])
        safe_with, _ = flt.is_safe_for_member(recipe_with_gluten, member)
        safe_without, _ = flt.is_safe_for_member(recipe_without, member)
        assert safe_with is False
        assert safe_without is True

    def test_household_filter(self):
        flt = AllergyFilter()
        m1 = _member(name="A", allergies=["noix"])
        m2 = _member(name="B")
        h = HouseholdProfile(members=[m1, m2])
        recipe = _recipe(ingredients=["50g de noix de cajou"])
        safe, reason = flt.is_safe_for_household(recipe, h)
        assert safe is False
        assert "A" in reason

    def test_filter_recipes(self):
        flt = AllergyFilter()
        h = HouseholdProfile(members=[_member(allergies=["saumon"])])
        recipes = [
            _recipe("Saumon grillé", ["300g de saumon"]),
            _recipe("Poulet rôti", ["500g de poulet"]),
        ]
        safe, rejected = flt.filter_recipes(recipes, h)
        assert len(safe) == 1
        assert len(rejected) == 1
        assert safe[0]["name"] == "Poulet rôti"


class TestRecipeScorer:
    def test_score_range(self):
        scorer = RecipeScorer()
        member = _member()
        recipe = _recipe(kcal=150)
        report = scorer.score(recipe, member, MealType.dinner)
        assert 0.0 <= report.score <= 1.0

    def test_score_zero_nutrition(self):
        scorer = RecipeScorer()
        member = _member()
        recipe = {"slug": "empty", "name": "Empty", "recipeServings": 1, "recipeIngredient": []}
        report = scorer.score(recipe, member, MealType.dinner)
        assert report.score == 0.0

    def test_score_for_household(self):
        scorer = RecipeScorer()
        members = [_member(name="A"), _member(name="B", sex=Sex.male, weight_kg=80, height_cm=178)]
        recipe = _recipe(kcal=200)
        score = scorer.score_for_household(recipe, members, MealType.lunch)
        assert 0.0 <= score <= 1.0

    def test_score_empty_household(self):
        scorer = RecipeScorer()
        assert scorer.score_for_household(_recipe(), [], MealType.dinner) == 0.0

    def test_calorie_fit_pct_populated(self):
        scorer = RecipeScorer()
        member = _member()
        report = scorer.score(recipe=_recipe(kcal=150), member=member, meal_type=MealType.dinner)
        assert report.calorie_fit_pct is not None
        assert report.calorie_fit_pct > 0
