from ingredient_price_collector.importers import import_observations_from_csv, import_observations_from_dicts


def test_import_dicts_accepts_aliases():
    result = import_observations_from_dicts([
        {
            "ingredient": "Oignons",
            "product": "Oignons jaunes",
            "price": "2.40",
            "quantity": "1",
            "unit": "kg",
            "store": "Carrefour",
            "date": "2026-05-07",
        }
    ])

    assert result.imported == 1
    assert result.rejected == 0
    assert result.observations[0].price_per_kg == 2.4
    assert result.observations[0].store_name == "Carrefour"


def test_import_csv_rejects_invalid_rows():
    content = b"ingredient_name,price_amount,package_quantity,package_unit\nOignons,2.40,1,kg\nSel,,1,kg\n"
    result = import_observations_from_csv(content)

    assert result.imported == 1
    assert result.rejected == 1
    assert result.observations[0].normalized_ingredient == "oignon"
