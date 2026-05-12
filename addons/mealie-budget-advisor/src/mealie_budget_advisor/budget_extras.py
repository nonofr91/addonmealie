"""Persistance des budgets dans le champ ``extras`` de la recette Mealie.

Utilise la fake recipe "💰 Budget Advisor" pour stocker les budgets mensuels
dans ses extras, avec préfixe ``budget_``.

Convention de nommage (toutes les clés en français, snake_case, préfixe ``budget_``) :

Clés écrites par l'addon :
- ``budget_{period}_total``      : budget total pour la période (€)
- ``budget_{period}_daily``      : budget journalier pour la période (€)
- ``budget_{period}_updated``    : timestamp ISO UTC de la mise à jour

Exemple pour mai 2025 :
- ``budget_2025-05_total``      : "500.00"
- ``budget_2025-05_daily``      : "16.13"
- ``budget_2025-05_updated``    : "2025-05-12T18:00:00Z"
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

import requests

from .models.budget import BudgetPeriod, BudgetSettings

logger = logging.getLogger(__name__)

PREFIX = "budget_"
FAKE_RECIPE_NAME = "💰 Budget Advisor"


def _fmt_float(value: float) -> str:
    """Formate un float en chaîne (2 décimales)."""
    return f"{value:.2f}"


def _parse_decimal(raw: str) -> Optional[float]:
    """Parse un nombre tolérant virgule décimale et espaces."""
    if raw is None:
        return None
    text = str(raw).strip().replace(" ", "").replace(",", ".")
    if not text:
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    if value != value:  # NaN
        return None
    return value


def build_budget_extras(budget: BudgetSettings) -> dict[str, str]:
    """Sérialise un BudgetSettings en dict prêt à patcher dans ``extras``.

    Args:
        budget: Configuration du budget à sauvegarder

    Returns:
        ``dict[str, str]`` contenant les clés préfixées ``budget_``
    """
    period_key = budget.period.period_label
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    return {
        f"{PREFIX}{period_key}_total": _fmt_float(budget.total_budget),
        f"{PREFIX}{period_key}_daily": _fmt_float(budget.budget_per_day),
        f"{PREFIX}{period_key}_updated": now,
    }


def read_budget_from_extras(
    extras: Optional[dict[str, str]], period: BudgetPeriod
) -> Optional[BudgetSettings]:
    """Extrait un budget depuis les ``extras`` d'une recette.

    Args:
        extras: Dictionnaire extras de la recette
        period: Période du budget à lire

    Returns:
        BudgetSettings ou None si non trouvé
    """
    if not extras:
        return None

    period_key = period.period_label
    total = _parse_decimal(extras.get(f"{PREFIX}{period_key}_total", ""))
    daily = _parse_decimal(extras.get(f"{PREFIX}{period_key}_daily", ""))

    if total is None:
        return None

    # BudgetSettings ne prend pas daily_limit en paramètre, budget_per_day est calculé
    return BudgetSettings(
        period=period,
        total_budget=total,
    )


class BudgetExtrasManager:
    """Gère la persistance des budgets dans les extras de la fake recipe Mealie."""

    def __init__(self, mealie_base_url: str, mealie_api_key: str):
        """Initialise le gestionnaire.

        Args:
            mealie_base_url: URL de base de l'API Mealie
            mealie_api_key: Clé API Mealie
        """
        self.mealie_base_url = mealie_base_url.rstrip("/")
        if self.mealie_base_url.endswith("/api"):
            self.mealie_base_url = self.mealie_base_url[:-4]
        self.headers = {
            "Authorization": f"Bearer {mealie_api_key}",
            "Content-Type": "application/json",
        }

    def _get_fake_recipe_slug(self) -> Optional[str]:
        """Récupère le slug de la fake recipe '💰 Budget Advisor'.

        Returns:
            Slug de la recette ou None si non trouvée
        """
        try:
            resp = requests.get(
                f"{self.mealie_base_url}/api/recipes",
                headers=self.headers,
                params={"search": FAKE_RECIPE_NAME, "perPage": 5},
                timeout=10,
            )
            resp.raise_for_status()
            for recipe in resp.json().get("items", []):
                if recipe.get("name") == FAKE_RECIPE_NAME:
                    return recipe.get("slug")
        except Exception as exc:
            logger.error("Erreur lors de la recherche de la fake recipe: %s", exc)
        return None

    def _get_recipe_extras(self, slug: str) -> Optional[dict[str, str]]:
        """Récupère les extras d'une recette.

        Args:
            slug: Slug de la recette

        Returns:
            Dictionnaire extras ou None
        """
        try:
            resp = requests.get(
                f"{self.mealie_base_url}/api/recipes/{slug}",
                headers=self.headers,
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json().get("extras")
        except Exception as exc:
            logger.error("Erreur lors de la récupération des extras: %s", exc)
            return None

    def _update_recipe_extras(self, slug: str, extras: dict[str, str]) -> bool:
        """Met à jour les extras d'une recette.

        Args:
            slug: Slug de la recette
            extras: Nouveau dictionnaire extras

        Returns:
            True si succès, False sinon
        """
        try:
            resp = requests.patch(
                f"{self.mealie_base_url}/api/recipes/{slug}",
                headers=self.headers,
                json={"extras": extras},
                timeout=10,
            )
            resp.raise_for_status()
            return True
        except Exception as exc:
            logger.error("Erreur lors de la mise à jour des extras: %s", exc)
            return False

    def set_budget(self, budget: BudgetSettings) -> bool:
        """Sauvegarde un budget dans les extras de la fake recipe.

        Args:
            budget: Configuration du budget à sauvegarder

        Returns:
            True si succès, False sinon
        """
        slug = self._get_fake_recipe_slug()
        if not slug:
            logger.error("Fake recipe '%s' non trouvée", FAKE_RECIPE_NAME)
            return False

        # Récupérer les extras existants
        existing_extras = self._get_recipe_extras(slug) or {}

        # Construire les nouveaux extras pour ce budget
        new_budget_extras = build_budget_extras(budget)

        # Fusionner (conserver les autres extras, remplacer ceux de ce budget)
        merged_extras = existing_extras.copy()
        merged_extras.update(new_budget_extras)

        # Mettre à jour
        if self._update_recipe_extras(slug, merged_extras):
            logger.info(
                "Budget sauvegardé dans extras pour %s: %.2f€",
                budget.period.period_label,
                budget.total_budget,
            )
            return True

        return False

    def get_budget(self, period: Optional[BudgetPeriod] = None) -> Optional[BudgetSettings]:
        """Récupère un budget depuis les extras de la fake recipe.

        Args:
            period: Période (par défaut: période actuelle)

        Returns:
            Configuration du budget ou None
        """
        if period is None:
            period = BudgetPeriod.current()

        slug = self._get_fake_recipe_slug()
        if not slug:
            logger.warning("Fake recipe '%s' non trouvée", FAKE_RECIPE_NAME)
            return None

        extras = self._get_recipe_extras(slug)
        if not extras:
            return None

        return read_budget_from_extras(extras, period)

    def delete_budget(self, period: BudgetPeriod) -> bool:
        """Supprime un budget des extras de la fake recipe.

        Args:
            period: Période à supprimer

        Returns:
            True si succès, False sinon
        """
        slug = self._get_fake_recipe_slug()
        if not slug:
            logger.error("Fake recipe '%s' non trouvée", FAKE_RECIPE_NAME)
            return False

        extras = self._get_recipe_extras(slug)
        if not extras:
            return False

        period_key = period.period_label
        keys_to_remove = [
            f"{PREFIX}{period_key}_total",
            f"{PREFIX}{period_key}_daily",
            f"{PREFIX}{period_key}_updated",
        ]

        removed = False
        for key in keys_to_remove:
            if key in extras:
                del extras[key]
                removed = True

        if removed and self._update_recipe_extras(slug, extras):
            logger.info("Budget supprimé des extras pour %s", period_key)
            return True

        return False

    def list_budgets(self) -> list[BudgetSettings]:
        """Liste tous les budgets sauvegardés dans les extras.

        Returns:
            Liste des configurations de budget
        """
        slug = self._get_fake_recipe_slug()
        if not slug:
            logger.warning("Fake recipe '%s' non trouvée", FAKE_RECIPE_NAME)
            return []

        extras = self._get_recipe_extras(slug)
        if not extras:
            return []

        budgets = []
        for key, value in extras.items():
            if key.startswith(f"{PREFIX}") and key.endswith("_total"):
                # Extraire la période: budget_2025-05_total -> 2025-05
                period_str = key[len(PREFIX) : -len("_total")]
                try:
                    year, month = map(int, period_str.split("-"))
                    period = BudgetPeriod(year=year, month=month)
                    budget = read_budget_from_extras(extras, period)
                    if budget:
                        budgets.append(budget)
                except (ValueError, IndexError):
                    logger.warning("Période invalide dans extras: %s", period_str)

        return sorted(budgets, key=lambda b: (b.period.year, b.period.month))
