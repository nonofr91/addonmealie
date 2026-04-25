"""Sérialisation / lecture des coûts de recettes dans le champ ``extras`` de Mealie.

Contraintes Mealie :
- ``extras`` est un ``dict[str, str]`` libre, affiché dans l'onglet *Propriétés*
  de chaque recette.
- Toutes les valeurs doivent être sérialisées en chaîne.

Convention de nommage (toutes les clés en français, snake_case, préfixe ``cout_``) :

Clés écrites par l'addon (peuvent être recalculées) :
- ``cout_total``              : coût total de la recette (€)
- ``cout_par_portion``        : coût par portion (€)
- ``cout_devise``             : devise (ex. ``EUR``)
- ``cout_confiance``          : confiance du calcul (0-1)
- ``cout_mois_reference``     : mois de référence du calcul (``YYYY-MM``)
- ``cout_calcule_le``         : timestamp ISO UTC du calcul
- ``cout_source``             : ``auto`` (calculé) ou ``manuel`` (override actif)

Clés réservées à l'utilisateur — l'addon ne les écrase jamais :
- ``cout_manuel_par_portion`` : override manuel du coût par portion
- ``cout_manuel_total``       : override manuel du coût total
- ``cout_manuel_raison``      : raison libre (ex. « promo Leclerc -30% »)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from .models.cost import RecipeCost

PREFIX = "cout_"

ADDON_KEYS: frozenset[str] = frozenset(
    {
        "cout_total",
        "cout_par_portion",
        "cout_devise",
        "cout_confiance",
        "cout_mois_reference",
        "cout_calcule_le",
        "cout_source",
    }
)

USER_KEYS: frozenset[str] = frozenset(
    {
        "cout_manuel_par_portion",
        "cout_manuel_total",
        "cout_manuel_raison",
    }
)


@dataclass(frozen=True)
class RecipeCostOverride:
    """Override manuel lu depuis les ``extras`` d'une recette."""

    per_serving: Optional[float] = None
    total: Optional[float] = None
    reason: Optional[str] = None

    @property
    def has_override(self) -> bool:
        return self.per_serving is not None or self.total is not None


def _fmt_float(value: float) -> str:
    """Formate un float en chaîne (2 décimales), évite les NaN/Inf."""
    if value != value or value in (float("inf"), float("-inf")):
        return "0.00"
    return f"{value:.2f}"


def build_addon_extras(
    cost: RecipeCost,
    month: Optional[str] = None,
    currency: str = "EUR",
    source: str = "auto",
    computed_at: Optional[datetime] = None,
) -> dict[str, str]:
    """Sérialise un :class:`RecipeCost` en dict prêt à patcher dans ``extras``.

    Args:
        cost: Coût calculé de la recette.
        month: Mois de référence au format ``YYYY-MM``. Si ``None``, mois courant UTC.
        currency: Devise à écrire (par défaut ``EUR``).
        source: ``auto`` ou ``manuel``.
        computed_at: Timestamp du calcul. Si ``None``, ``datetime.utcnow()``.

    Returns:
        ``dict[str, str]`` contenant uniquement les clés préfixées ``cout_``
        écrites par l'addon (jamais les clés utilisateur).
    """
    now = computed_at or datetime.now(timezone.utc)
    if month is None:
        month = now.strftime("%Y-%m")

    return {
        "cout_total": _fmt_float(cost.total_cost),
        "cout_par_portion": _fmt_float(cost.cost_per_serving),
        "cout_devise": currency,
        "cout_confiance": _fmt_float(cost.confidence),
        "cout_mois_reference": month,
        "cout_calcule_le": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "cout_source": source,
    }


def merge_extras(
    existing: Optional[dict[str, str]],
    new_addon_extras: dict[str, str],
) -> dict[str, str]:
    """Fusionne les nouveaux ``extras`` calculés avec ceux déjà présents.

    - Les clés non-addon sont **conservées telles quelles**.
    - Les clés utilisateur (``cout_manuel_*``) sont **toujours préservées**.
    - Les clés addon (``cout_*`` listées dans :data:`ADDON_KEYS`) sont remplacées.

    Args:
        existing: Dictionnaire ``extras`` déjà sur la recette (peut être ``None``).
        new_addon_extras: Dictionnaire produit par :func:`build_addon_extras`.

    Returns:
        Dictionnaire fusionné prêt à patcher.
    """
    result: dict[str, str] = {}
    if existing:
        for key, value in existing.items():
            if value is None:
                continue
            result[str(key)] = str(value)

    for key, value in new_addon_extras.items():
        if key in ADDON_KEYS:
            result[key] = str(value)

    # Les clés utilisateur présentes dans `existing` sont déjà conservées par la
    # boucle initiale (elles ne sont jamais dans ADDON_KEYS).
    return result


def _parse_decimal(raw: str) -> Optional[float]:
    """Parse un nombre tolérant virgule décimale et espaces (``'1,07'`` → ``1.07``)."""
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


def read_override(extras: Optional[dict[str, str]]) -> RecipeCostOverride:
    """Extrait un éventuel override manuel depuis les ``extras`` d'une recette.

    - Accepte la virgule décimale (``'1,07'``) et les espaces.
    - Les valeurs non numériques sont ignorées silencieusement.

    Priorité de lecture (utilisée par le planner) :
        1. ``cout_manuel_par_portion``
        2. ``cout_manuel_total`` (divisé par ``servings`` côté appelant si besoin)
    """
    if not extras:
        return RecipeCostOverride()

    per_serving = _parse_decimal(extras.get("cout_manuel_par_portion", ""))
    total = _parse_decimal(extras.get("cout_manuel_total", ""))
    reason_raw = extras.get("cout_manuel_raison", "")
    reason = str(reason_raw).strip() or None if reason_raw is not None else None

    return RecipeCostOverride(per_serving=per_serving, total=total, reason=reason)
