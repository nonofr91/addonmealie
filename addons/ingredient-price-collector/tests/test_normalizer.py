from ingredient_price_collector.models import PriceObservationCreate
from ingredient_price_collector.normalizer import normalize_ingredient_name, normalize_observation


def test_normalize_ingredient_name_removes_accents_and_plural():
    assert normalize_ingredient_name("Oignons jaunes") == "oignons jaune"


def test_normalize_observation_computes_price_per_kg():
    observation = normalize_observation(
        PriceObservationCreate(
            ingredient_name="Oignons",
            product_name="Oignons jaunes",
            price_amount=2.40,
            package_quantity=1,
            package_unit="kg",
        )
    )

    assert observation.normalized_ingredient == "oignon"
    assert observation.price_per_kg == 2.4
    assert observation.price_per_l is None
    assert observation.price_per_piece is None
    assert observation.confidence == 0.95


def test_ai_estimate_confidence_is_capped():
    observation = normalize_observation(
        PriceObservationCreate(
            ingredient_name="Safran",
            source="ai_estimate",
            price_amount=12,
            package_quantity=1,
            package_unit="g",
            confidence=0.9,
        )
    )

    assert observation.confidence == 0.5
    assert "ai_estimate_confidence_capped" in observation.quality_flags


def test_price_below_category_bounds_reduces_confidence():
    observation = normalize_observation(
        PriceObservationCreate(
            ingredient_name="Oignons",
            source="open_prices",
            price_amount=0.20,
            package_quantity=1,
            package_unit="kg",
        )
    )

    assert "price_below_category_bounds" in observation.quality_flags
    assert observation.confidence < 0.7


def test_price_above_category_bounds_reduces_confidence():
    observation = normalize_observation(
        PriceObservationCreate(
            ingredient_name="Bœuf",
            source="open_prices",
            price_amount=100.0,
            package_quantity=1,
            package_unit="kg",
        )
    )

    assert "price_above_category_bounds" in observation.quality_flags
    assert observation.confidence < 0.7
