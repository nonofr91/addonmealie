"""Planificateur pour le rafraîchissement mensuel automatique des coûts.

Utilise APScheduler (BackgroundScheduler) pour exécuter une tâche cron qui
recalcule le coût de toutes les recettes et le publie dans ``extras`` de Mealie.

Activé par défaut (1er du mois à 03:00 UTC), désactivable via
``ENABLE_MONTHLY_COST_REFRESH=false``.
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


def _parse_cron(expression: str) -> dict[str, str]:
    """Convertit une expression cron 5-champs en kwargs ``CronTrigger``.

    Format attendu : ``"minute hour day month day_of_week"``
    Exemple : ``"0 3 1 * *"`` → 1er du mois à 03:00.
    """
    parts = expression.strip().split()
    if len(parts) != 5:
        raise ValueError(
            f"Expression cron invalide (5 champs attendus): {expression!r}"
        )
    minute, hour, day, month, dow = parts
    return {
        "minute": minute,
        "hour": hour,
        "day": day,
        "month": month,
        "day_of_week": dow,
    }


class BudgetScheduler:
    """Wrapper APScheduler pour le rafraîchissement mensuel des coûts."""

    def __init__(
        self,
        refresh_callable: Callable[[], dict],
        cron_expression: str = "0 3 1 * *",
        timezone: str = "UTC",
    ) -> None:
        """Initialise le scheduler.

        Args:
            refresh_callable: Fonction appelée par le job (attendu : retourne un dict).
            cron_expression: Expression cron 5-champs.
            timezone: Fuseau horaire APScheduler (par défaut UTC).
        """
        self.refresh_callable = refresh_callable
        self.cron_expression = cron_expression
        self.timezone = timezone
        self._scheduler: Optional[object] = None

    def _run_job(self) -> None:
        """Wrapper d'exécution : log + capture d'exception pour ne pas tuer APScheduler."""
        logger.info("Démarrage du rafraîchissement mensuel des coûts (cron)")
        try:
            summary = self.refresh_callable()
            logger.info("Rafraîchissement mensuel terminé: %s", summary)
        except Exception:  # noqa: BLE001 — on protège le scheduler
            logger.exception("Échec du rafraîchissement mensuel des coûts")

    def start(self) -> None:
        """Démarre le scheduler (idempotent)."""
        if self._scheduler is not None:
            logger.debug("Scheduler déjà démarré, rien à faire")
            return

        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger
        except ImportError as exc:
            logger.warning(
                "APScheduler non installé (%s), cron mensuel désactivé. "
                "Installez avec : pip install apscheduler",
                exc,
            )
            return

        trigger_kwargs = _parse_cron(self.cron_expression)
        trigger = CronTrigger(timezone=self.timezone, **trigger_kwargs)

        scheduler = BackgroundScheduler(timezone=self.timezone)
        scheduler.add_job(
            self._run_job,
            trigger=trigger,
            id="monthly-cost-refresh",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )
        scheduler.start()
        self._scheduler = scheduler
        logger.info(
            "Scheduler démarré (cron=%r, tz=%s)", self.cron_expression, self.timezone
        )

    def shutdown(self) -> None:
        """Arrête proprement le scheduler."""
        if self._scheduler is None:
            return
        try:
            self._scheduler.shutdown(wait=False)  # type: ignore[attr-defined]
            logger.info("Scheduler arrêté")
        except Exception:  # noqa: BLE001
            logger.exception("Erreur lors de l'arrêt du scheduler")
        finally:
            self._scheduler = None
