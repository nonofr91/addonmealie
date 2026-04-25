"""CLI du Budget Advisor : synchronisation des coûts vers Mealie (``extras``).

Sous-commandes :
- ``mealie-budget sync-cost <slug> [--month YYYY-MM]`` :
    recalcule et publie dans ``extras`` la recette indiquée.
- ``mealie-budget refresh-costs [--month YYYY-MM]`` :
    recalcule et publie pour toutes les recettes.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Optional

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mealie-budget",
        description="CLI Budget Advisor — synchronisation des coûts dans Mealie extras.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sync = sub.add_parser(
        "sync-cost",
        help="Recalcule et publie le coût d'une recette dans extras.cout_*",
    )
    sync.add_argument("slug", help="Slug de la recette Mealie")
    sync.add_argument(
        "--month",
        default=None,
        help="Mois de référence au format YYYY-MM (défaut: mois courant UTC)",
    )
    sync.add_argument(
        "--no-open-prices",
        action="store_true",
        help="Désactive le fallback Open Prices (prix manuels uniquement)",
    )

    refresh = sub.add_parser(
        "refresh-costs",
        help="Recalcule et publie les coûts pour toutes les recettes Mealie",
    )
    refresh.add_argument(
        "--month",
        default=None,
        help="Mois de référence au format YYYY-MM (défaut: mois courant UTC)",
    )
    refresh.add_argument(
        "--no-open-prices",
        action="store_true",
        help="Désactive le fallback Open Prices (prix manuels uniquement)",
    )

    return parser


def _print_json(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def main(argv: Optional[list[str]] = None) -> int:
    """Point d'entrée CLI (``mealie-budget``)."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Import tardif : éviter d'initier la config tant qu'aucune commande n'a été parsée.
    from .config import BudgetConfigError, get_config

    try:
        config = get_config()
    except BudgetConfigError as exc:
        print(f"Erreur de configuration: {exc}", file=sys.stderr)
        return 2

    from .mealie_sync import MealieClient
    from .pricing.cost_calculator import CostCalculator

    client = MealieClient(config.mealie_base_url, config.mealie_api_key)
    calculator = CostCalculator(config.mealie_base_url, config.mealie_api_key)

    use_open_prices = not getattr(args, "no_open_prices", False)

    if args.command == "sync-cost":
        result = calculator.sync_recipe_cost(
            slug=args.slug,
            month=args.month,
            use_open_prices=use_open_prices,
            mealie_client=client,
        )
        _print_json(result)
        return 0 if result.get("success") else 1

    if args.command == "refresh-costs":
        summary = calculator.refresh_all_costs(
            month=args.month,
            use_open_prices=use_open_prices,
            mealie_client=client,
        )
        _print_json({"success": True, "summary": summary})
        return 0

    parser.error(f"Commande inconnue: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
