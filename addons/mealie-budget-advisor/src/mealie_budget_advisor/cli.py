"""Command-line interface for the mealie-budget-advisor addon."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .models.budget import BudgetSettings
from .models.pricing import ManualPrice
from .orchestrator import BudgetOrchestrator


def _print(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mealie-budget", description="Mealie Budget Advisor CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Afficher le statut de l'addon")

    p_budget_get = sub.add_parser("budget-get", help="Afficher le budget d'un mois")
    p_budget_get.add_argument("--month", default=None, help="Mois au format YYYY-MM")

    p_budget_set = sub.add_parser("budget-set", help="Définir le budget d'un mois")
    p_budget_set.add_argument("--month", required=True, help="YYYY-MM")
    p_budget_set.add_argument("--total", required=True, type=float, help="Budget total en €")
    p_budget_set.add_argument("--forfait", default=20.0, type=float, help="Forfait condiments")
    p_budget_set.add_argument("--meals", default=3, type=int)
    p_budget_set.add_argument("--days", default=30, type=int)
    p_budget_set.add_argument("--currency", default="EUR")

    p_price = sub.add_parser("price-add", help="Ajouter un prix manuel")
    p_price.add_argument("--name", required=True)
    p_price.add_argument("--unit", required=True, help="kg / l / unit")
    p_price.add_argument("--price", required=True, type=float)
    p_price.add_argument("--currency", default="EUR")
    p_price.add_argument("--note", default=None)

    p_cost = sub.add_parser("recipe-cost", help="Calculer le coût d'une recette")
    p_cost.add_argument("slug")

    p_plan = sub.add_parser("plan", help="Planifier un menu respectant le budget")
    p_plan.add_argument("--month", default=None)
    p_plan.add_argument("--meals", default=None, type=int)

    args = parser.parse_args(argv)
    orch = BudgetOrchestrator()

    if args.command == "status":
        _print(orch.get_status())
        return 0

    if args.command == "budget-get":
        settings = orch.get_budget(args.month)
        _print(settings.model_dump())
        return 0

    if args.command == "budget-set":
        settings = BudgetSettings(
            month=args.month,
            total_budget=args.total,
            condiments_forfait=args.forfait,
            meals_per_day=args.meals,
            days_per_month=args.days,
            currency=args.currency,
        )
        _print(orch.set_budget(settings).model_dump())
        return 0

    if args.command == "price-add":
        price = ManualPrice(
            ingredient_name=args.name,
            unit=args.unit,
            price_per_unit=args.price,
            currency=args.currency,
            note=args.note,
        )
        _print(orch.manual_pricer.upsert(price).model_dump(mode="json"))
        return 0

    if args.command == "recipe-cost":
        cost = orch.cost_recipe(args.slug)
        _print(cost.model_dump(mode="json"))
        return 0

    if args.command == "plan":
        report = orch.plan_budget_aware(month=args.month, meals_target=args.meals)
        _print(report.model_dump(mode="json"))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
