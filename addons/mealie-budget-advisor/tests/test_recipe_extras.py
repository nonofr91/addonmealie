"""Tests unitaires pour le module ``recipe_extras`` (sérialisation extras Mealie)."""

from __future__ import annotations

from mealie_budget_advisor.models.cost import RecipeCost
from mealie_budget_advisor.recipe_extras import (
    ADDON_KEYS,
    KEY_CALCULE_LE,
    KEY_CONFIANCE,
    KEY_DEVISE,
    KEY_MANUEL_PAR_PORTION,
    KEY_MANUEL_RAISON,
    KEY_MANUEL_TOTAL,
    KEY_MOIS,
    KEY_PAR_PORTION,
    KEY_SOURCE,
    KEY_TOTAL,
    USER_KEYS,
    build_addon_extras,
    merge_extras,
    read_override,
)


def _cost(total: float = 2.15, per_serving: float = 1.07) -> RecipeCost:
    return RecipeCost(
        recipe_slug="poulet-riz",
        recipe_name="Poulet riz",
        servings=2,
        total_cost=total,
        cost_per_serving=per_serving,
        currency="EUR",
        confidence=1.0,
    )


# ------------------------------------------------------------------- build


def test_build_addon_extras_contient_toutes_les_cles_addon():
    extras = build_addon_extras(_cost(), month="2026-04")

    assert set(extras.keys()) == ADDON_KEYS
    assert extras[KEY_TOTAL] == "2.15"
    assert extras[KEY_PAR_PORTION] == "1.07"
    assert extras[KEY_DEVISE] == "EUR"
    assert extras[KEY_CONFIANCE] == "1.00"
    assert extras[KEY_MOIS] == "2026-04"
    assert extras[KEY_SOURCE] == "auto"
    # Horodatage ISO8601 UTC
    assert extras[KEY_CALCULE_LE].endswith("Z")
    assert "T" in extras[KEY_CALCULE_LE]


def test_build_addon_extras_ne_contient_aucune_cle_utilisateur():
    extras = build_addon_extras(_cost(), month="2026-04")
    assert USER_KEYS.isdisjoint(extras.keys())


# ------------------------------------------------------------------- merge


def test_merge_extras_preserve_cles_tierces():
    existing = {
        "nutrition_calories": "450",        # clé d'un autre addon
        "emoji": "🍗",                      # clé libre
        KEY_TOTAL: "99.99",                 # clé addon -> sera écrasée
    }
    new_addon = build_addon_extras(_cost(), month="2026-04")

    merged = merge_extras(existing, new_addon)

    assert merged["nutrition_calories"] == "450"
    assert merged["emoji"] == "🍗"
    assert merged[KEY_TOTAL] == "2.15"


def test_merge_extras_preserve_override_utilisateur():
    existing = {
        KEY_MANUEL_PAR_PORTION: "1.50",
        KEY_MANUEL_TOTAL: "3.00",
        KEY_MANUEL_RAISON: "promo Leclerc",
        KEY_PAR_PORTION: "9.99",  # ancienne valeur auto, sera écrasée
    }
    new_addon = build_addon_extras(_cost(), month="2026-04")

    merged = merge_extras(existing, new_addon)

    assert merged[KEY_MANUEL_PAR_PORTION] == "1.50"
    assert merged[KEY_MANUEL_TOTAL] == "3.00"
    assert merged[KEY_MANUEL_RAISON] == "promo Leclerc"
    assert merged[KEY_PAR_PORTION] == "1.07"


def test_merge_extras_sur_dict_none_ou_vide():
    new_addon = build_addon_extras(_cost(), month="2026-04")

    assert merge_extras(None, new_addon) == new_addon
    assert merge_extras({}, new_addon) == new_addon


def test_merge_extras_cast_valeurs_en_str():
    # Mealie n'accepte que des strings dans extras
    existing: dict = {"foo": 42, "bar": None}
    new_addon = build_addon_extras(_cost(), month="2026-04")

    merged = merge_extras(existing, new_addon)
    assert all(isinstance(v, str) for v in merged.values())


# ------------------------------------------------------------------- read_override


def test_read_override_inactif_si_extras_vides():
    ov = read_override(None)
    assert ov.is_active is False
    assert ov.per_serving is None
    assert ov.total is None

    ov = read_override({})
    assert ov.is_active is False


def test_read_override_par_portion():
    ov = read_override({KEY_MANUEL_PAR_PORTION: "2.50"})
    assert ov.is_active is True
    assert ov.per_serving == 2.50
    assert ov.total is None


def test_read_override_accepte_virgule_decimale():
    ov = read_override({KEY_MANUEL_PAR_PORTION: "2,50"})
    assert ov.per_serving == 2.50


def test_read_override_ignore_valeur_invalide():
    ov = read_override({KEY_MANUEL_PAR_PORTION: "pas-un-nombre"})
    assert ov.is_active is False


def test_read_override_total_et_raison():
    ov = read_override(
        {
            KEY_MANUEL_TOTAL: "5.00",
            KEY_MANUEL_RAISON: "courses vrac",
        }
    )
    assert ov.is_active is True
    assert ov.total == 5.00
    assert ov.raison == "courses vrac"
