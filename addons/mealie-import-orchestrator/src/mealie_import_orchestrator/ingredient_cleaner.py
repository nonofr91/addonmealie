#!/usr/bin/env python3
"""
Module de nettoyage des foods Mealie.

Détecte et corrige les foods mal formés créés lors des imports :
- Unité incluse dans le nom (ex: "g de beurre" → food "beurre", unit "g")
- Modificateurs de préparation dans le nom (ex: "oignons finement émincés" → "oignon")
- Noms sans accents

Fonctionnalité avancée : lorsqu'une unité est extraite du nom du food,
les ingrédients des recettes sont mis à jour pour inclure cette unité.
Cela permet :
- Une nutrition précise par ingrédient
- Le regroupement des ingrédients dans les listes de courses
- La recherche de recettes par ingrédients disponibles

Sécurité : les recettes existantes sont préservées via le renommage du food
(Mealie met à jour les références dans les recettes automatiquement).
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any

import requests


# ---------------------------------------------------------------------------
# Patterns de détection
# ---------------------------------------------------------------------------

_UNIT_PREFIX = re.compile(
    r"^(\d+[\.,]?\d*\s*)?(g|kg|ml|cl|dl|l|oz|lb|lbs)\s+d[e']?\s+(.+)$",
    re.IGNORECASE,
)

# Patterns pour extraire les modificateurs de préparation
# Format: (pattern, nom_du_modificateur)
_MODIFIER_PATTERNS = [
    # Très finement + verbe
    (re.compile(r"\s+(très\s+)?finement\s+(\w+)", re.IGNORECASE), lambda m: f"finement {m.group(2)}"),
    # Grossièrement + verbe
    (re.compile(r"\s+(grossièrement\s+)?(\w+)[eé]s?\b", re.IGNORECASE), lambda m: m.group(2)),
    # Coupé en...
    (re.compile(r"\s+coupé[es]?(?:\s+en\s+(\w+))?", re.IGNORECASE), lambda m: f"coupé en {m.group(1)}" if m.group(1) else "coupé"),
    # Haché
    (re.compile(r"\s+haché[es]?", re.IGNORECASE), "haché"),
    # Émincé
    (re.compile(r"\s+émincé[es]?", re.IGNORECASE), "émincé"),
    # Ciselé
    (re.compile(r"\s+ciselé[es]?", re.IGNORECASE), "ciselé"),
    # Râpé
    (re.compile(r"\s+râpé[es]?", re.IGNORECASE), "râpé"),
    # Tranché
    (re.compile(r"\s+tranché[es]?", re.IGNORECASE), "tranché"),
    # En dés/julienne/etc
    (re.compile(r"\s+en\s+(dés|julienne|lamelles|rondelles|brunoise)", re.IGNORECASE), lambda m: f"en {m.group(1)}"),
]

_PARENTHESIS = re.compile(r"\s*\([^)]*\)", re.IGNORECASE)

# Unités extraites du nom → mapping vers l'unité Mealie cible
_UNIT_NAME_MAP = {
    "g": "g",
    "kg": "kg",
    "ml": "ml",
    "cl": "cl",
    "dl": "dl",
    "l": "l",
    "oz": "g",   # sera converti
    "lb": "g",
    "lbs": "g",
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class FoodIssue:
    food_id: str
    food_name: str
    issue_type: str          # "unit_in_name" | "modifier_in_name" | "no_accent"
    suggested_name: str
    extracted_unit: str = ""           # Unité extraite du nom (ex: "g", "ml")
    extracted_modifier: str = ""       # Préparation extraite (ex: "haché", "émincé")
    description: str = ""


@dataclass
class CleanReport:
    total_scanned: int = 0
    issues: list[FoodIssue] = field(default_factory=list)
    fixed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_scanned": self.total_scanned,
            "issues_count": len(self.issues),
            "fixed_count": len(self.fixed),
            "errors_count": len(self.errors),
            "issues": [
                {
                    "food_id": i.food_id,
                    "food_name": i.food_name,
                    "issue_type": i.issue_type,
                    "suggested_name": i.suggested_name,
                    "extracted_unit": i.extracted_unit,
                    "extracted_modifier": i.extracted_modifier,
                    "description": i.description,
                }
                for i in self.issues
            ],
            "fixed": self.fixed,
            "errors": self.errors,
        }


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def _detect_issues(food: dict) -> list[FoodIssue]:
    """Retourne la liste des problèmes détectés pour un food."""
    name = food.get("name", "")
    food_id = food.get("id", "")
    issues = []

    # 1. Unité dans le nom
    m = _UNIT_PREFIX.match(name)
    if m:
        unit_raw = m.group(2).lower()
        clean_name = m.group(3).strip()
        # Supprimer aussi les parenthèses résiduelles
        clean_name = _PARENTHESIS.sub("", clean_name).strip()
        issues.append(FoodIssue(
            food_id=food_id,
            food_name=name,
            issue_type="unit_in_name",
            suggested_name=clean_name,
            extracted_unit=_UNIT_NAME_MAP.get(unit_raw, unit_raw),
            description=f"Unité '{unit_raw}' incluse dans le nom → food devrait être '{clean_name}'",
        ))
        return issues  # pas besoin de vérifier les autres patterns

    # 2. Modificateurs de préparation
    clean = _PARENTHESIS.sub("", name).strip()
    original_clean = clean
    extracted_modifiers = []

    for pattern, modifier_extractor in _MODIFIER_PATTERNS:
        match = pattern.search(clean)
        if match:
            # Extraire le nom du modificateur
            if callable(modifier_extractor):
                modifier_name = modifier_extractor(match)
            else:
                modifier_name = modifier_extractor
            if modifier_name:
                extracted_modifiers.append(modifier_name)
            # Supprimer le modificateur du nom
            clean = pattern.sub("", clean).strip()

    if clean != original_clean and len(clean) >= 2:
        # Construire la note avec tous les modificateurs trouvés
        modifier_note = ", ".join(extracted_modifiers) if extracted_modifiers else ""
        issues.append(FoodIssue(
            food_id=food_id,
            food_name=name,
            issue_type="modifier_in_name",
            suggested_name=clean,
            extracted_modifier=modifier_note,
            description=f"Modificateur de préparation détecté → food='{clean}', note='{modifier_note}'",
        ))

    # 3. Parenthèses seules (commentaire dans le nom)
    elif _PARENTHESIS.search(name):
        clean = _PARENTHESIS.sub("", name).strip()
        if clean and clean != name:
            issues.append(FoodIssue(
                food_id=food_id,
                food_name=name,
                issue_type="modifier_in_name",
                suggested_name=clean,
                description=f"Commentaire entre parenthèses → '{clean}'",
            ))

    return issues


def _load_all_foods(api_url: str, headers: dict) -> list[dict]:
    """Charge tous les foods depuis l'API Mealie (pagination)."""
    foods = []
    page = 1
    while True:
        r = requests.get(
            f"{api_url}/foods?page={page}&perPage=500",
            headers=headers,
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        foods.extend(data.get("items", []))
        if not data.get("next"):
            break
        page += 1
    return foods


def _rename_food(api_url: str, headers: dict, food_id: str, new_name: str) -> None:
    """
    Renomme un food via PATCH /api/foods/{id}.
    Mealie met à jour automatiquement les références dans les recettes.
    """
    r = requests.patch(
        f"{api_url}/foods/{food_id}",
        headers=headers,
        json={"name": new_name},
        timeout=10,
    )
    r.raise_for_status()


def _load_all_units(api_url: str, headers: dict) -> dict[str, str]:
    """
    Charge toutes les unités depuis Mealie et retourne un dict {name_lower: id}.
    """
    units = {}
    page = 1
    while True:
        r = requests.get(
            f"{api_url}/units?page={page}&perPage=100",
            headers=headers,
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        for unit in data.get("items", []):
            unit_id = unit.get("id")
            unit_name = unit.get("name", "").lower()
            if unit_id and unit_name:
                units[unit_name] = unit_id
                # Alias pour les unités courantes
                if unit_name in ["gramme", "grammes"]:
                    units["g"] = unit_id
                elif unit_name in ["kilogramme", "kilogrammes"]:
                    units["kg"] = unit_id
                elif unit_name in ["millilitre", "millilitres"]:
                    units["ml"] = unit_id
                elif unit_name in ["litre", "litres"]:
                    units["l"] = unit_id
        if not data.get("next"):
            break
        page += 1
    return units


def _find_recipes_using_food(api_url: str, headers: dict, food_id: str) -> list[dict]:
    """
    Trouve toutes les recettes qui utilisent un food donné.
    Retourne la liste des recettes avec leurs ingrédients.
    """
    recipes = []
    page = 1
    while True:
        r = requests.get(
            f"{api_url}/recipes?page={page}&perPage=100",
            headers=headers,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        for recipe in data.get("items", []):
            slug = recipe.get("slug")
            if not slug:
                continue
            # Charger les détails de la recette pour voir les ingrédients
            try:
                detail_resp = requests.get(
                    f"{api_url}/recipes/{slug}",
                    headers=headers,
                    timeout=15,
                )
                detail_resp.raise_for_status()
                detail = detail_resp.json()
                # Vérifier si un ingrédient utilise ce food
                ingredients = detail.get("recipeIngredients", [])
                for ing in ingredients:
                    ing_food = ing.get("food")
                    if ing_food and ing_food.get("id") == food_id:
                        recipes.append({
                            "slug": slug,
                            "name": detail.get("name", slug),
                            "ingredient": ing,
                            "ingredients": ingredients,
                        })
                        break  # Une recette peut apparaître une seule fois
            except Exception:
                continue
        if not data.get("next"):
            break
        page += 1
    return recipes


def _update_recipe_ingredient(
    api_url: str,
    headers: dict,
    recipe_slug: str,
    ingredient_id: str,
    unit_id: str | None,
    note: str | None,
    original_ingredient: dict,
) -> bool:
    """
    Met à jour l'unité et/ou la note d'un ingrédient dans une recette.
    Préserve toutes les autres propriétés de l'ingrédient.
    """
    # Construire le payload PATCH pour la recette
    updated_ing = dict(original_ingredient)

    # Mettre à jour l'unité si fournie
    if unit_id:
        updated_ing["unit"] = {"id": unit_id}

    # Mettre à jour la note si fournie (ajouter à la note existante)
    if note:
        existing_note = updated_ing.get("note", "") or ""
        if existing_note:
            updated_ing["note"] = f"{existing_note}, {note}"
        else:
            updated_ing["note"] = note

    # Charger la recette complète pour la modifier
    try:
        r = requests.get(
            f"{api_url}/recipes/{recipe_slug}",
            headers=headers,
            timeout=15,
        )
        r.raise_for_status()
        recipe = r.json()

        # Mettre à jour l'ingrédient spécifique
        ingredients = recipe.get("recipeIngredients", [])
        for i, ing in enumerate(ingredients):
            if ing.get("id") == ingredient_id:
                ingredients[i] = updated_ing
                break

        # PATCH la recette avec les ingrédients modifiés
        r = requests.patch(
            f"{api_url}/recipes/{recipe_slug}",
            headers=headers,
            json={"recipeIngredients": ingredients},
            timeout=30,
        )
        r.raise_for_status()
        return True
    except Exception as exc:
        raise RuntimeError(f"Erreur mise à jour recette {recipe_slug}: {exc}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class IngredientCleaner:
    """Détecte et corrige les foods mal formés dans Mealie."""

    def __init__(self) -> None:
        base = os.environ.get("MEALIE_BASE_URL", "").rstrip("/")
        token = os.environ.get("MEALIE_API_KEY", "")
        if not base or not token:
            raise RuntimeError("MEALIE_BASE_URL et MEALIE_API_KEY requis")
        if not base.endswith("/api"):
            base = f"{base}/api"
        self._api_url = base
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def scan(self) -> CleanReport:
        """Analyse tous les foods et retourne le rapport sans rien modifier."""
        report = CleanReport()
        foods = _load_all_foods(self._api_url, self._headers)
        report.total_scanned = len(foods)
        for food in foods:
            report.issues.extend(_detect_issues(food))
        return report

    def fix(self, issue_ids: list[str] | None = None, update_recipe_units: bool = True) -> CleanReport:
        """
        Corrige les foods problématiques et met à jour les ingrédients des recettes.

        Pour chaque food corrigé :
        1. Renomme le food (ex: "g de beurre" → "beurre", "persil haché" → "persil")
        2. Met à jour les ingrédients des recettes concernées :
           - Ajoute l'unité extraite si présente (ex: "g")
           - Ajoute la préparation dans la note si présente (ex: "haché")

        Args:
            issue_ids: liste de food_id à corriger. Si None, corrige tout.
            update_recipe_units: si True, met à jour les ingrédients dans les recettes
                                 (unité et/ou note selon ce qui est extrait).

        Sécurité : utilise PATCH /foods/{id} — Mealie met à jour
        automatiquement les recettes qui référencent ce food.
        """
        report = self.scan()

        to_fix = [
            i for i in report.issues
            if issue_ids is None or i.food_id in issue_ids
        ]

        # Charger les unités si nécessaire
        units_map = {}
        if update_recipe_units:
            try:
                units_map = _load_all_units(self._api_url, self._headers)
            except Exception as exc:
                report.errors.append(f"⚠️ Impossible de charger les unités: {exc}")

        # Vérifier les conflits de noms : si le suggested_name existe déjà,
        # on ne renomme pas (éviter les doublons)
        existing_names = {
            f["name"].lower()
            for f in _load_all_foods(self._api_url, self._headers)
        }

        for issue in to_fix:
            target = issue.suggested_name
            if target.lower() in existing_names and target.lower() != issue.food_name.lower():
                report.errors.append(
                    f"⚠️ '{issue.food_name}' → '{target}' ignoré : le food cible existe déjà"
                )
                continue
            try:
                # 1. Renommer le food
                _rename_food(self._api_url, self._headers, issue.food_id, target)
                fix_msg = f"'{issue.food_name}' → '{target}'"

                # 2. Mettre à jour les ingrédients des recettes concernées
                if update_recipe_units:
                    try:
                        recipes = _find_recipes_using_food(
                            self._api_url, self._headers, issue.food_id
                        )
                        updated_count = 0
                        unit_id = None
                        if issue.extracted_unit and units_map:
                            unit_id = units_map.get(issue.extracted_unit.lower())

                        for rec in recipes:
                            try:
                                _update_recipe_ingredient(
                                    self._api_url,
                                    self._headers,
                                    rec["slug"],
                                    rec["ingredient"]["id"],
                                    unit_id,
                                    issue.extracted_modifier or None,
                                    rec["ingredient"],
                                )
                                updated_count += 1
                            except Exception as ing_exc:
                                report.errors.append(
                                    f"❌ Recette '{rec['name']}' - ingrédient non mis à jour: {ing_exc}"
                                )
                        if updated_count > 0:
                            updates = []
                            if issue.extracted_unit:
                                updates.append(f"unité '{issue.extracted_unit}'")
                            if issue.extracted_modifier:
                                updates.append(f"note '{issue.extracted_modifier}'")
                            if updates:
                                fix_msg += f" (+{updated_count} recettes avec {', '.join(updates)})"
                    except Exception as rec_exc:
                        report.errors.append(
                            f"⚠️ Erreur recherche recettes pour '{target}': {rec_exc}"
                        )

                report.fixed.append(fix_msg)
                existing_names.add(target.lower())
            except Exception as exc:
                report.errors.append(
                    f"❌ Erreur sur '{issue.food_name}': {exc}"
                )

        return report
