"""Tests for the nutrition calculation engine."""

import pytest

from mealie_nutrition_advisor.models.nutrition import NutritionFacts, NutritionSource
from mealie_nutrition_advisor.nutrition.ai_estimator import AIEstimator
from mealie_nutrition_advisor.nutrition.cache import NutritionCache
from mealie_nutrition_advisor.nutrition.calculator import NutritionCalculator
from mealie_nutrition_advisor.nutrition.ingredient_parser import parse_ingredient


class TestIngredientParser:
    def test_grams_explicit(self):
        parsed = parse_ingredient("200g de poulet haché")
        assert parsed.quantity_g == pytest.approx(200.0)
        assert "poulet" in parsed.food_name.lower()

    def test_tablespoon(self):
        parsed = parse_ingredient("2 cuillères à soupe d'huile d'olive")
        assert parsed.quantity_g == pytest.approx(30.0)

    def test_no_unit(self):
        parsed = parse_ingredient("1 oignon moyen")
        assert parsed.quantity_g > 0

    def test_empty_string(self):
        parsed = parse_ingredient("")
        assert parsed.food_name == ""
        assert parsed.quantity_g > 0

    def test_fraction_comma(self):
        parsed = parse_ingredient("1,5 kg de farine")
        assert parsed.quantity_g == pytest.approx(1500.0)


class TestNutritionFacts:
    def test_scale(self):
        facts = NutritionFacts(calories_kcal=200, protein_g=10, fat_g=5, carbohydrate_g=30)
        scaled = facts.scale(0.5)
        assert scaled.calories_kcal == pytest.approx(100.0)
        assert scaled.protein_g == pytest.approx(5.0)

    def test_add(self):
        a = NutritionFacts(calories_kcal=100, protein_g=10)
        b = NutritionFacts(calories_kcal=200, protein_g=20)
        total = a + b
        assert total.calories_kcal == pytest.approx(300.0)
        assert total.protein_g == pytest.approx(30.0)

    def test_is_empty(self):
        assert NutritionFacts().is_empty()
        assert not NutritionFacts(calories_kcal=100).is_empty()


class TestAIEstimatorMock:
    def test_returns_facts(self):
        estimator = AIEstimator(provider="mock")
        facts = estimator.estimate("poulet")
        assert facts is not None
        assert facts.calories_kcal > 0
        assert facts.source == NutritionSource.ai_estimate

    def test_default_fallback(self):
        estimator = AIEstimator(provider="mock")
        facts = estimator.estimate("ingrédient inconnu xyz123")
        assert facts is not None
        assert facts.calories_kcal > 0


class TestNutritionCache:
    def test_set_get(self, tmp_path):
        cache = NutritionCache(cache_path=tmp_path / "cache.json")
        facts = NutritionFacts(calories_kcal=150, protein_g=10, source=NutritionSource.ai_estimate)
        cache.set("pomme", facts)
        result = cache.get("pomme")
        assert result is not None
        assert result.calories_kcal == pytest.approx(150.0)

    def test_cache_miss(self, tmp_path):
        cache = NutritionCache(cache_path=tmp_path / "cache.json")
        assert cache.get("xyz_missing") is None

    def test_normalize_key(self, tmp_path):
        cache = NutritionCache(cache_path=tmp_path / "cache.json")
        facts = NutritionFacts(calories_kcal=100)
        cache.set("  Pomme  ", facts)
        result = cache.get("pomme")
        assert result is not None

    def test_save_and_reload(self, tmp_path):
        path = tmp_path / "cache.json"
        cache = NutritionCache(cache_path=path)
        facts = NutritionFacts(calories_kcal=99, protein_g=3)
        cache.set("carotte", facts)
        cache.save()

        cache2 = NutritionCache(cache_path=path)
        result = cache2.get("carotte")
        assert result is not None
        assert result.calories_kcal == pytest.approx(99.0)


class TestNutritionCalculator:
    def test_calculate_recipe_mock(self, tmp_path):
        cache = NutritionCache(cache_path=tmp_path / "cache.json")
        estimator = AIEstimator(provider="mock")
        calculator = NutritionCalculator(cache=cache, ai_estimator=estimator)

        result = calculator.calculate_recipe(
            recipe_slug="poulet-rotii",
            recipe_name="Poulet Rôti",
            ingredient_texts=["800g de poulet", "2 cuillères à soupe d'huile", "sel"],
            servings=4,
        )
        assert result.per_serving.calories_kcal > 0
        assert len(result.ingredients) == 3
        assert result.servings == 4

    def test_mealie_nutrition_format(self, tmp_path):
        cache = NutritionCache(cache_path=tmp_path / "cache.json")
        estimator = AIEstimator(provider="mock")
        calculator = NutritionCalculator(cache=cache, ai_estimator=estimator)

        result = calculator.calculate_recipe(
            recipe_slug="test",
            recipe_name="Test",
            ingredient_texts=["100g beurre"],
            servings=1,
        )
        mealie_fmt = result.to_mealie_nutrition()
        assert "calories" in mealie_fmt
        assert "proteinContent" in mealie_fmt
        assert "fatContent" in mealie_fmt
        assert "carbohydrateContent" in mealie_fmt
