"""Planificateur de tâches périodiques pour l'addon budget.

Utilise APScheduler (``BackgroundScheduler``) démarré avec le processus
FastAPI. Aujourd'hui une seule tâche est programmée : le rafraîchissement
mensuel des coûts (``cout_*``) dans les extras des recettes Mealie.

Activation et expression cron pilotées par ``BudgetConfig`` :
- ``ENABLE_MONTHLY_COST_REFRESH`` (bool, défaut ``true``)
- ``MONTHLY_COST_REFRESH_CRON`` (expression cron 5-champs, défaut
  ``0 3 1 * *`` — 1er du mois à 03:00 UTC)
"""

from __future__ import annotations

import logging
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import BudgetConfig
from .orchestrator import BudgetOrchestrator

logger = logging.getLogger(__name__)


def _parse_cron(expression: str) -> CronTrigger:
    """Parse une expression cron 5-champs (minute heure jour mois jour-semaine)."""
    parts = expression.strip().split()
    if len(parts) != 5:
        raise ValueError(
            f"Expression cron invalide (5 champs attendus) : {expression!r}"
        )
    minute, hour, day, month, day_of_week = parts
    return CronTrigger(
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=day_of_week,
    )


def _refresh_costs_job(orchestrator: BudgetOrchestrator) -> None:
    """Job planifié — délègue à l'orchestrator."""
    try:
        report = orchestrator.refresh_all_costs()
        logger.info("Refresh mensuel OK: %s", report)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Refresh mensuel KO: %s", exc)


class BudgetScheduler:
    """Wrapper fin autour de ``BackgroundScheduler``."""

    def __init__(self, orchestrator: BudgetOrchestrator, config: BudgetConfig) -> None:
        self.orchestrator = orchestrator
        self.config = config
        self._scheduler: Optional[BackgroundScheduler] = None

    def start(self) -> bool:
        """Démarre le planificateur si la feature est activée."""
        if not self.config.enable_monthly_cost_refresh:
            logger.info("ENABLE_MONTHLY_COST_REFRESH=false — planificateur désactivé")
            return False

        try:
            trigger = _parse_cron(self.config.monthly_cost_refresh_cron)
        except ValueError as exc:
            logger.warning("Cron invalide: %s — planificateur non démarré", exc)
            return False

        scheduler = BackgroundScheduler(timezone="UTC")
        scheduler.add_job(
            _refresh_costs_job,
            trigger=trigger,
            id="monthly_cost_refresh",
            args=[self.orchestrator],
            replace_existing=True,
            misfire_grace_time=3600,
            coalesce=True,
        )
        scheduler.start()
        self._scheduler = scheduler
        logger.info(
            "Planificateur démarré: refresh mensuel cron='%s' (UTC)",
            self.config.monthly_cost_refresh_cron,
        )
        return True

    def stop(self) -> None:
        if self._scheduler is not None:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
            logger.info("Planificateur arrêté")
