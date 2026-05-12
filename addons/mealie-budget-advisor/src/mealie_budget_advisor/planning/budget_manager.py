"""Gestionnaire de budget mensuel avec persistance JSON ou Mealie extras."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from mealie_budget_advisor.models.budget import BudgetPeriod, BudgetSettings

logger = logging.getLogger(__name__)


class BudgetManager:
    """Gère le budget mensuel avec persistance JSON ou Mealie extras."""

    def __init__(
        self,
        config_dir: Optional[Path] = None,
        use_extras: bool = False,
        mealie_base_url: Optional[str] = None,
        mealie_api_key: Optional[str] = None,
    ) -> None:
        """Initialise le gestionnaire de budget.

        Args:
            config_dir: Répertoire de configuration (par défaut: ./config)
            use_extras: Si True, utilise Mealie extras pour la persistance
            mealie_base_url: URL de base de l'API Mealie (requis si use_extras=True)
            mealie_api_key: Clé API Mealie (requis si use_extras=True)
        """
        self.config_dir = config_dir or Path("config")
        self.config_dir.mkdir(exist_ok=True)
        self.budget_file = self.config_dir / "budgets.json"
        self._budgets: dict[str, dict] = {}
        self._use_extras = use_extras
        self._extras_manager = None

        if self._use_extras:
            if not mealie_base_url or not mealie_api_key:
                logger.warning(
                    "use_extras=True mais mealie_base_url ou mealie_api_key manquant, fallback sur JSON"
                )
                self._use_extras = False
            else:
                try:
                    from ..budget_extras import BudgetExtrasManager

                    self._extras_manager = BudgetExtrasManager(mealie_base_url, mealie_api_key)
                    logger.info("BudgetManager: utilisation de Mealie extras pour la persistance")
                except ImportError:
                    logger.warning("BudgetExtrasManager non disponible, fallback sur JSON")
                    self._use_extras = False

        if not self._use_extras:
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
        if self._use_extras and self._extras_manager:
            if self._extras_manager.set_budget(budget):
                logger.info("Budget défini pour %s: %.2f€ (via extras)", budget.period.period_label, budget.total_budget)
                return budget
            else:
                logger.warning("Échec de la sauvegarde via extras, fallback sur JSON")
                self._use_extras = False

        period_key = budget.period.period_label
        self._budgets[period_key] = budget.model_dump(mode="json")
        self._save_budgets()
        logger.info("Budget défini pour %s: %.2f€ (via JSON)", period_key, budget.total_budget)
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

        if self._use_extras and self._extras_manager:
            budget = self._extras_manager.get_budget(period)
            if budget:
                logger.debug("Budget récupéré pour %s via extras", period.period_label)
                return budget
            logger.debug("Budget non trouvé pour %s via extras", period.period_label)

        period_key = period.period_label
        budget_data = self._budgets.get(period_key)

        if budget_data:
            logger.debug("Budget récupéré pour %s via JSON", period_key)
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
        if self._use_extras and self._extras_manager:
            if self._extras_manager.delete_budget(period):
                logger.info("Budget supprimé pour %s (via extras)", period.period_label)
                return True

        period_key = period.period_label
        if period_key in self._budgets:
            del self._budgets[period_key]
            self._save_budgets()
            logger.info("Budget supprimé pour %s (via JSON)", period_key)
            return True
        return False

    def list_budgets(self) -> list[BudgetSettings]:
        """Liste tous les budgets sauvegardés.

        Returns:
            Liste des configurations de budget
        """
        if self._use_extras and self._extras_manager:
            budgets = self._extras_manager.list_budgets()
            if budgets:
                logger.debug("%d budgets listés via extras", len(budgets))
                return budgets
            logger.debug("Aucun budget listé via extras")

        budgets = []
        for period_key, budget_data in self._budgets.items():
            try:
                budgets.append(BudgetSettings(**budget_data))
            except Exception as e:
                logger.error("Erreur lors du parsing du budget %s: %s", period_key, e)
        logger.debug("%d budgets listés via JSON", len(budgets))
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
