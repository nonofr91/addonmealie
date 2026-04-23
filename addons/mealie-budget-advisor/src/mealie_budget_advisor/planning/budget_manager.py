"""Gestionnaire de budget mensuel avec persistance."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from mealie_budget_advisor.models.budget import BudgetPeriod, BudgetSettings

logger = logging.getLogger(__name__)


class BudgetManager:
    """Gère le budget mensuel avec persistance JSON."""

    def __init__(self, config_dir: Optional[Path] = None) -> None:
        """Initialise le gestionnaire de budget.

        Args:
            config_dir: Répertoire de configuration (par défaut: ./config)
        """
        self.config_dir = config_dir or Path("config")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.budget_file = self.config_dir / "budgets.json"
        self._budgets: dict[str, dict] = {}
        self._load_budgets()

    def _load_budgets(self) -> None:
        """Charge les budgets depuis le fichier JSON."""
        if self.budget_file.exists():
            try:
                with open(self.budget_file, encoding="utf-8") as f:
                    self._budgets = json.load(f)
                logger.info("Chargé %d budgets depuis %s", len(self._budgets), self.budget_file)
            except Exception as e:
                logger.error("Erreur lors du chargement des budgets: %s", e)
                self._budgets = {}

    def _save_budgets(self) -> None:
        """Sauvegarde les budgets dans le fichier JSON."""
        try:
            with open(self.budget_file, "w", encoding="utf-8") as f:
                json.dump(self._budgets, f, indent=2, ensure_ascii=False)
            logger.info("Sauvegardé %d budgets dans %s", len(self._budgets), self.budget_file)
        except Exception as e:
            logger.error("Erreur lors de la sauvegarde des budgets: %s", e)

    def set_budget(self, budget: BudgetSettings) -> BudgetSettings:
        """Définit le budget pour une période.

        Args:
            budget: Configuration du budget

        Returns:
            Le budget sauvegardé
        """
        period_key = budget.period.period_label
        self._budgets[period_key] = budget.model_dump()
        self._save_budgets()
        logger.info("Budget défini pour %s: %.2f€", period_key, budget.total_budget)
        return budget

    def get_budget(self, period: Optional[BudgetPeriod] = None) -> Optional[BudgetSettings]:
        """Récupère le budget pour une période.

        Args:
            period: Période (par défaut: période actuelle)

        Returns:
            Configuration du budget ou None
        """
        if period is None:
            period = BudgetPeriod.current()

        period_key = period.period_label
        budget_data = self._budgets.get(period_key)

        if budget_data:
            return BudgetSettings(**budget_data)

        return None

    def get_current_budget(self) -> Optional[BudgetSettings]:
        """Récupère le budget de la période actuelle.

        Returns:
            Configuration du budget actuel ou None
        """
        return self.get_budget(BudgetPeriod.current())

    def delete_budget(self, period: BudgetPeriod) -> bool:
        """Supprime le budget pour une période.

        Args:
            period: Période à supprimer

        Returns:
            True si supprimé, False si non trouvé
        """
        period_key = period.period_label
        if period_key in self._budgets:
            del self._budgets[period_key]
            self._save_budgets()
            logger.info("Budget supprimé pour %s", period_key)
            return True
        return False

    def list_budgets(self) -> list[BudgetSettings]:
        """Liste tous les budgets sauvegardés.

        Returns:
            Liste des configurations de budget
        """
        budgets = []
        for period_key, budget_data in self._budgets.items():
            try:
                budgets.append(BudgetSettings(**budget_data))
            except Exception as e:
                logger.error("Erreur lors du parsing du budget %s: %s", period_key, e)
        return sorted(budgets, key=lambda b: (b.period.year, b.period.month))

    def get_statistics(self) -> dict:
        """Retourne des statistiques sur les budgets.

        Returns:
            Dictionnaire avec les statistiques
        """
        budgets = self.list_budgets()
        return {
            "total_budgets": len(budgets),
            "current_budget": self.get_current_budget() is not None,
            "periods": [b.period.period_label for b in budgets],
        }
