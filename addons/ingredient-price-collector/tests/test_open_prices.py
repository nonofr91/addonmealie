from ingredient_price_collector.collectors.open_prices import OpenPricesCollector


def test_open_prices_collector_returns_observations():
    collector = OpenPricesCollector()
    observations = collector.search("oignons", limit=2, currency="EUR")

    assert isinstance(observations, list)
    if observations:
        obs = observations[0]
        assert obs.ingredient_name == "oignons"
        assert obs.source.value == "open_prices"
        assert obs.confidence == 0.7


def test_open_prices_collector_filters_invalid_prices():
    collector = OpenPricesCollector()
    observations = collector.search("oignons", limit=10, currency="EUR")

    for obs in observations:
        assert obs.price_amount > 0
        assert obs.package_quantity > 0
