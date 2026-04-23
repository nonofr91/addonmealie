"""Sérialisation / lecture du coût d'une recette dans Mealie `extras`.

Mealie expose un champ ``extras`` libre (dict[str, str]) par recette.
On l'utilise pour publier le coût calculé — lisible et éditable dans l'UI
Mealie (onglet « Propriétés ») — en préfixant toutes nos clés par ``cout_``.

Règles :
- Toutes les valeurs sont sérialisées en chaînes (contrainte Mealie).
- Seules les clés préfixées ``cout_`` sont écrites ; les autres extras
  existants sont préservés lors d'un patch.
- ``cout_manuel_par_portion`` et ``cout_manuel_raison`` ne sont JAMAIS
  écrits par l'addon — ils sont réservés à une édition manuelle de
  l'utilisateur dans Mealie et gagnent toujours face au coût calculé.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from .models.cost import RecipeCost

# --------------------------------------------------------------------- schéma

PREFIX = "cout_"

# Clés écrites par l'addon (calcul automatique)
KEY_TOTAL = "cout_total"
KEY_PAR_PORTION = "cout_par_portion"
KEY_DEVISE = "cout_devise"
KEY_CONFIANCE = "cout_confiance"
KEY_MOIS = "cout_mois_reference"
KEY_CALCULE_LE = "cout_calcule_le"
KEY_SOURCE = "cout_source"            # "auto" ou "manuel"

# Clés réservées à l'utilisateur (édition manuelle via Mealie)
KEY_MANUEL_PAR_PORTION = "cout_manuel_par_portion"
KEY_MANUEL_TOTAL = "cout_manuel_total"
KEY_MANUEL_RAISON = "cout_manuel_raison"

USER_KEYS = frozenset({
    KEY_MANUEL_PAR_PORTION,
    KEY_MANUEL_TOTAL,
    KEY_MANUEL_RAISON,
})

ADDON_KEYS = frozenset({
    KEY_TOTAL,
    KEY_PAR_PORTION,
    KEY_DEVISE,
    KEY_CONFIANCE,
    KEY_MOIS,
    KEY_CALCULE_LE,
    KEY_SOURCE,
})


# ----------------------------------------------------------------- sérialisation


def build_addon_extras(cost: RecipeCost, month: Optional[str]) -> dict[str, str]:
    """Construit le payload ``extras`` à écrire pour un coût calculé.

    Ne contient QUE les clés addon (``cout_*`` hors clés utilisateur).
    """
    return {
        KEY_TOTAL: f"{cost.total_cost:.2f}",
        KEY_PAR_PORTION: f"{cost.cost_per_serving:.2f}",
        KEY_DEVISE: cost.currency,
        KEY_CONFIANCE: f"{cost.confidence:.2f}",
        KEY_MOIS: month or "",
        KEY_CALCULE_LE: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        KEY_SOURCE: "auto",
    }


def merge_extras(existing: Optional[dict], new_addon_extras: dict[str, str]) -> dict[str, str]:
    """Fusionne les extras existants avec les clés addon recalculées.

    - Les extras non préfixés ``cout_`` sont préservés tels quels.
    - Les clés utilisateur (``cout_manuel_*``) sont préservées tels quels.
    - Les clés addon (``cout_*`` hors utilisateur) sont écrasées.
    """
    merged: dict[str, str] = {}
    for k, v in (existing or {}).items():
        if not isinstance(k, str):
            continue
        # On garde tout ce qui n'est PAS une clé addon
        if k in ADDON_KEYS:
            continue
        merged[k] = v if isinstance(v, str) else str(v)

    merged.update(new_addon_extras)
    return merged


# ----------------------------------------------------------------- désérialisation


@dataclass(frozen=True)
class RecipeCostOverride:
    """Coût manuel lu depuis les extras Mealie."""

    per_serving: Optional[float]
    total: Optional[float]
    raison: Optional[str]

    @property
    def is_active(self) -> bool:
        return self.per_serving is not None or self.total is not None


def _parse_float(raw: object) -> Optional[float]:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str):
        s = raw.strip().replace(",", ".")
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            return None
    return None


def read_override(extras: Optional[dict]) -> RecipeCostOverride:
    """Lit un éventuel override manuel dans les extras d'une recette."""
    extras = extras or {}
    return RecipeCostOverride(
        per_serving=_parse_float(extras.get(KEY_MANUEL_PAR_PORTION)),
        total=_parse_float(extras.get(KEY_MANUEL_TOTAL)),
        raison=(extras.get(KEY_MANUEL_RAISON) or None) if isinstance(extras.get(KEY_MANUEL_RAISON), str) else None,
    )
