from __future__ import annotations

import argparse
import contextlib
import json
import sys

from .config import AddonConfig, AddonConfigurationError
from .orchestrator import AddonExecutionError, MealieImportOrchestrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mealie-import-orchestrator")
    parser.add_argument("--workflow-directory", dest="workflow_directory")

    subparsers = parser.add_subparsers(dest="command", required=True)

    full_parser = subparsers.add_parser("full")
    full_parser.add_argument("--source", dest="sources", action="append")

    step_parser = subparsers.add_parser("step")
    step_parser.add_argument("step", choices=["scraping", "structuring", "importing", "scrape"])
    step_parser.add_argument("--source", dest="sources", action="append")
    step_parser.add_argument("--scraped-filename", dest="scraped_filename", type=str, help='Fichier JSON scrapé pour la structuration')
    step_parser.add_argument("--structured-filename", dest="structured_filename", type=str, help='Fichier JSON structuré pour l\'import')
    step_parser.add_argument("--scrape-url", dest="scrape_url", type=str, help='URL à scraper avec les MCP Jina via Cascade')

    subparsers.add_parser("status")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "step" and args.step == "structuring" and not args.scraped_filename:
            raise AddonConfigurationError(
                "The structuring step requires --scraped-filename in addon runtime."
            )

        if args.command == "step" and args.step == "importing" and not args.structured_filename:
            raise AddonConfigurationError(
                "The importing step requires --structured-filename in addon runtime."
            )

        config = AddonConfig.load(workflow_directory=args.workflow_directory)
        orchestrator = MealieImportOrchestrator(config=config)

        with contextlib.redirect_stdout(sys.stderr):
            if args.command == "full":
                result = orchestrator.run_full_workflow(sources=args.sources)
            elif args.command == "step":
                result = orchestrator.run_workflow_step(
                    args.step,
                    sources=args.sources,
                    scraped_filename=args.scraped_filename,
                    structured_filename=args.structured_filename,
                )
            else:
                result = orchestrator.get_status()
    except (AddonConfigurationError, AddonExecutionError) as exc:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": str(exc),
                },
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("success", True) else 1
