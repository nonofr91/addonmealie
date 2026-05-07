"""Tests pour le module ingredient_matcher."""

import pytest

from mealie_budget_advisor.pricing.ingredient_matcher import IngredientMatcher
from mealie_budget_advisor.pricing.ingredient_weights import get_ingredient_weight


class TestIngredientMatcher:
    """Tests pour IngredientMatcher."""

    @pytest.fixture
    def matcher(self):
        """Fixture pour IngredientMatcher."""
        return IngredientMatcher()

    def test_parse_simple_quantity(self, matcher):
        """Test parsing simple: '200g de farine'."""
        qty, unit, name = matcher.parse_ingredient_note("200g de farine")
        assert qty == 200.0
        assert unit == "g"
        assert name == "farine"

    def test_parse_with_space(self, matcher):
        """Test parsing avec espace: '200 g farine'."""
        qty, unit, name = matcher.parse_ingredient_note("200 g farine")
        assert qty == 200.0
        assert unit == "g"
        assert name == "farine"

    def test_parse_fraction(self, matcher):
        """Test parsing avec fraction: '1/2 tasse de lait'."""
        qty, unit, name = matcher.parse_ingredient_note("1/2 tasse de lait")
        assert qty == 0.5
        assert unit == "cup"
        assert name == "lait"

    def test_parse_fraction_3_4(self, matcher):
        """Test parsing avec fraction 3/4: '3/4 cup sugar'."""
        qty, unit, name = matcher.parse_ingredient_note("3/4 cup sugar")
        assert qty == 0.75
        assert unit == "cup"
        assert name == "sugar"

    def test_parse_french_decimal(self, matcher):
        """Test parsing décimale française: '2,5 kg de pommes'."""
        qty, unit, name = matcher.parse_ingredient_note("2,5 kg de pommes")
        assert qty == 2.5
        assert unit == "kg"
        assert name == "pommes"

    def test_parse_cuillere_soupe(self, matcher):
        """Test parsing cuillère à soupe: '2 cuillères à soupe d'huile'."""
        qty, unit, name = matcher.parse_ingredient_note("2 cuillères à soupe d'huile")
        assert qty == 2.0
        assert unit == "tbsp"
        assert name == "huile"

    def test_parse_cuillere_cafe(self, matcher):
        """Test parsing cuillère à café: '1 cuillère à café de sucre'."""
        qty, unit, name = matcher.parse_ingredient_note("1 cuillère à café de sucre")
        assert qty == 1.0
        assert unit == "tsp"
        assert name == "sucre"

    def test_parse_abbreviated_cs(self, matcher):
        """Test parsing abrégé: '2 c. à s. huile'."""
        qty, unit, name = matcher.parse_ingredient_note("2 c. à s. huile")
        assert qty == 2.0
        assert unit == "tbsp"
        assert name == "huile"

    def test_parse_unit_only(self, matcher):
        """Test parsing sans unité: '2 pommes'."""
        qty, unit, name = matcher.parse_ingredient_note("2 pommes")
        assert qty == 2.0
        assert unit == "unit"
        assert name == "pommes"

    def test_parse_name_only(self, matcher):
        """Test parsing sans quantité: 'huile d'olive'."""
        qty, unit, name = matcher.parse_ingredient_note("huile d'olive")
        assert qty == 1.0
        assert unit == "unit"
        assert name == "huile d'olive"

    def test_normalize_unit_g(self, matcher):
        """Test normalisation unité g."""
        base_qty, base_unit = matcher.normalize_quantity(1000.0, "g")
        assert base_qty == 1.0
        assert base_unit == "kg"

    def test_normalize_unit_kg(self, matcher):
        """Test normalisation unité kg."""
        base_qty, base_unit = matcher.normalize_quantity(2.0, "kg")
        assert base_qty == 2.0
        assert base_unit == "kg"

    def test_normalize_unit_ml(self, matcher):
        """Test normalisation unité ml."""
        base_qty, base_unit = matcher.normalize_quantity(1000.0, "ml")
        assert base_qty == 1.0
        assert base_unit == "l"

    def test_normalize_unit_tbsp(self, matcher):
        """Test normalisation unité tbsp."""
        base_qty, base_unit = matcher.normalize_quantity(2.0, "tbsp")
        assert base_qty == 30.0
        assert base_unit == "ml"

    def test_normalize_unit_tsp(self, matcher):
        """Test normalisation unité tsp."""
        base_qty, base_unit = matcher.normalize_quantity(1.0, "tsp")
        assert base_qty == 5.0
        assert base_unit == "ml"

    def test_match_ingredient_to_product(self, matcher):
        """Test matching ingrédient ↔ produit."""
        candidates = ["Farine de blé", "Huile d'olive", "Sucre blanc"]
        match, score = matcher.match_ingredient_to_product("farine", candidates)
        assert match == "Farine de blé"
        assert score >= 70.0

    def test_match_no_candidates(self, matcher):
        """Test matching sans candidats."""
        result = matcher.match_ingredient_to_product("farine", [])
        assert result is None

    def test_normalize_ingredient_name(self, matcher):
        """Test normalisation nom ingrédient."""
        normalized = matcher._normalize_ingredient_name("le farine bio")
        assert normalized == "farine"

    def test_normalize_with_accents(self, matcher):
        """Test normalisation avec accents."""
        normalized = matcher._normalize_ingredient_name("crème fraîche")
        assert normalized == "creme fraiche"

    def test_unit_weights_for_small_culinary_items(self):
        assert get_ingredient_weight("oignons") == 0.15
        assert get_ingredient_weight("gousses d'ail") == 0.005
        assert get_ingredient_weight("feuilles de laurier") == 0.001
        assert get_ingredient_weight("genièvre") == 0.0002
        assert get_ingredient_weight("clous de girofle") == 0.0002
        assert get_ingredient_weight("bouillon de volaille") == 0.01

    def test_unit_weight_prefers_specific_match(self):
        assert get_ingredient_weight("1 gousse d'ail") == 0.005
        assert get_ingredient_weight("3 baies de genièvre") == 0.0002

    def test_estimate_price_vegetables(self, matcher):
        """Test estimation prix légumes."""
        price, source, confidence = matcher._estimate_price("tomates", 1.0, "kg")
        assert price > 0
        assert source == "estimated"
        assert 0 <= confidence <= 1

    def test_estimate_price_meat(self, matcher):
        """Test estimation prix viande."""
        price, source, confidence = matcher._estimate_price("bœuf", 1.0, "kg")
        assert price > 0
        assert source == "estimated"
        # La viande est généralement plus chère que les légumes
        assert price > matcher._estimate_price("tomates", 1.0, "kg")[0]
