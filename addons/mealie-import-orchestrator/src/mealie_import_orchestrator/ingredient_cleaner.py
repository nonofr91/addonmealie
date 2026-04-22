#!/usr/bin/env python3
"""
Module de nettoyage des foods Mealie.

Détecte et corrige les foods mal formés créés lors des imports :
- Unité incluse dans le nom (ex: "g de beurre" → food "beurre", unit "g")
- Modificateurs de préparation dans le nom (ex: "oignons finement émincés" → "oignon")
- Noms sans accents

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

_MODIFIER_PATTERNS = [
    (re.compile(r"\s+(très\s+)?finement\s+\w+", re.IGNORECASE), ""),
    (re.compile(r"\s+(grossièrement\s+)?\w*[eé]s?\b", re.IGNORECASE), None),  # géré séparément
    (re.compile(r"\s+coupé[es]?\s+(en\s+\w+)?", re.IGNORECASE), ""),
    (re.compile(r"\s+haché[es]?", re.IGNORECASE), ""),
    (re.compile(r"\s+émincé[es]?", re.IGNORECASE), ""),
    (re.compile(r"\s+ciselé[es]?", re.IGNORECASE), ""),
    (re.compile(r"\s+râpé[es]?", re.IGNORECASE), ""),
    (re.compile(r"\s+tranché[es]?", re.IGNORECASE), ""),
    (re.compile(r"\s+en\s+(dés|julienne|lamelles|rondelles|brunoise)", re.IGNORECASE), ""),
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
    extracted_unit: str = ""
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
    for pattern, replacement in _MODIFIER_PATTERNS:
        if replacement is not None and pattern.search(clean):
            clean = pattern.sub(replacement, clean).strip()

    if clean != original_clean and len(clean) >= 2:
        issues.append(FoodIssue(
            food_id=food_id,
            food_name=name,
            issue_type="modifier_in_name",
            suggested_name=clean,
            description=f"Modificateur de préparation détecté → '{clean}'",
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

    def fix(self, issue_ids: list[str] | None = None) -> CleanReport:
        """
        Corrige les foods problématiques.

        Args:
            issue_ids: liste de food_id à corriger. Si None, corrige tout.

        Sécurité : utilise PATCH /foods/{id} — Mealie met à jour
        automatiquement les recettes qui référencent ce food.
        """
        report = self.scan()

        to_fix = [
            i for i in report.issues
            if issue_ids is None or i.food_id in issue_ids
        ]

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
                _rename_food(self._api_url, self._headers, issue.food_id, target)
                report.fixed.append(
                    f"'{issue.food_name}' → '{target}'"
                )
                existing_names.add(target.lower())
            except Exception as exc:
                report.errors.append(
                    f"❌ Erreur sur '{issue.food_name}': {exc}"
                )

        return report
