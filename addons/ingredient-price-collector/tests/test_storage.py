from ingredient_price_collector.models import PriceObservationCreate
from ingredient_price_collector.normalizer import normalize_observation
from ingredient_price_collector.storage import PriceStorage


def test_storage_adds_and_searches_observations(tmp_path):
    storage = PriceStorage(tmp_path / "prices.sqlite3")
    observation = normalize_observation(
        PriceObservationCreate(
            ingredient_name="Oignons",
            product_name="Oignons jaunes",
            price_amount=2.40,
            package_quantity=1,
            package_unit="kg",
            store_name="Carrefour",
        )
    )

    storage.add_observations([observation])
    results = storage.search("oignon", unit="kg")

    assert storage.count_observations() == 1
    assert len(results) == 1
    assert results[0].price_per_kg == 2.4
    assert results[0].store_name == "Carrefour"


def test_storage_lists_anomalies(tmp_path):
    storage = PriceStorage(tmp_path / "prices.sqlite3")
    observation = normalize_observation(
        PriceObservationCreate(
            ingredient_name="Truffe",
            price_amount=500,
            package_quantity=1,
            package_unit="kg",
        )
    )

    storage.add_observations([observation])
    anomalies = storage.anomalies()

    assert len(anomalies) == 1
    assert "price_per_kg_outlier" in anomalies[0].quality_flags
