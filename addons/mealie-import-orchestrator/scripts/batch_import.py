#!/usr/bin/env python3
"""
Batch import de recettes Marmiton scrappées → Import + Nutrition + Coûts.

Lit le JSON produit par scrape_marmiton_urls.py et traite les recettes
par lots de N. Après chaque recette importée : nutrition. Après chaque
lot : calcul des coûts via le budget advisor.

Un fichier checkpoint (data/batch_import_checkpoint.json) permet de
reprendre l'exécution là où elle s'est arrêtée.

Usage:
    python3 scripts/batch_import.py --input data/marmiton_urls_2026-05-14.json
    python3 scripts/batch_import.py --input data/marmiton_urls_2026-05-14.json \\
        --categories entree dessert --batch-size 10 --delay-recipe 3
    python3 scripts/batch_import.py --resume      # reprend depuis le checkpoint
    python3 scripts/batch_import.py --dry-run     # affiche sans importer

Variables d'environnement (ou .env) :
    IMPORT_API_URL     URL du mealie-import-orchestrator (ex: http://localhost:8000)
    IMPORT_API_KEY     X-Addon-Key de l'import orchestrator
    BUDGET_API_URL     URL du mealie-budget-advisor (ex: http://localhost:8003)
    BUDGET_API_KEY     X-Addon-Key du budget advisor (optionnel)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

IMPORT_API_URL = os.environ.get("IMPORT_API_URL", "http://localhost:8000")
IMPORT_API_KEY = os.environ.get("IMPORT_API_KEY", "")
BUDGET_API_URL = os.environ.get("BUDGET_API_URL", "http://localhost:8003")
BUDGET_API_KEY = os.environ.get("BUDGET_API_KEY", "")

DATA_DIR = Path(__file__).parent.parent / "data"
CHECKPOINT_FILE = DATA_DIR / "batch_import_checkpoint.json"


def _import_headers() -> dict:
    h = {"Content-Type": "application/json"}
    if IMPORT_API_KEY:
        h["X-Addon-Key"] = IMPORT_API_KEY
    return h


def _budget_headers() -> dict:
    h = {"Content-Type": "application/json"}
    if BUDGET_API_KEY:
        h["X-Addon-Key"] = BUDGET_API_KEY
    return h


# ---------------------------------------------------------------------------
# API calls
# ---------------------------------------------------------------------------


def import_recipe(url: str, session: requests.Session) -> dict:
    """POST /import — retourne {success, slug, ...}."""
    try:
        resp = session.post(
            f"{IMPORT_API_URL}/import",
            json={"url": url},
            headers=_import_headers(),
            timeout=120,
        )
        if resp.status_code == 200:
            return resp.json()
        return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except requests.RequestException as exc:
        return {"success": False, "error": str(exc)}


def enrich_nutrition(slug: str, session: requests.Session) -> dict:
    """POST /nutrition/recipe/{slug}."""
    try:
        resp = session.post(
            f"{IMPORT_API_URL}/nutrition/recipe/{slug}",
            headers=_import_headers(),
            timeout=60,
        )
        if resp.status_code == 200:
            return resp.json()
        return {"success": False, "error": f"HTTP {resp.status_code}"}
    except requests.RequestException as exc:
        return {"success": False, "error": str(exc)}


def enrich_costs_batch(slugs: list[str], session: requests.Session) -> dict:
    """POST /recipes/batch-cost sur le budget advisor."""
    if not slugs or not BUDGET_API_URL:
        return {"skipped": True}
    try:
        resp = session.post(
            f"{BUDGET_API_URL}/recipes/batch-cost",
            json=slugs,
            headers=_budget_headers(),
            timeout=120,
        )
        if resp.status_code == 200:
            return resp.json()
        return {"success": False, "error": f"HTTP {resp.status_code}"}
    except requests.RequestException as exc:
        return {"success": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# Checkpoint
# ---------------------------------------------------------------------------


def load_checkpoint() -> dict:
    if CHECKPOINT_FILE.exists():
        return json.loads(CHECKPOINT_FILE.read_text())
    return {"processed_urls": {}, "created_at": datetime.now().isoformat()}


def save_checkpoint(checkpoint: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    checkpoint["updated_at"] = datetime.now().isoformat()
    CHECKPOINT_FILE.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# Batch processing
# ---------------------------------------------------------------------------


def process_batch(
    recipes: list[dict],
    checkpoint: dict,
    *,
    dry_run: bool,
    delay_recipe: float,
    skip_nutrition: bool,
    skip_costs: bool,
) -> list[str]:
    """Traite un lot de recettes. Retourne les slugs importés avec succès."""
    imported_slugs: list[str] = []

    with requests.Session() as session:
        for i, recipe in enumerate(recipes):
            url = recipe["url"]
            name = recipe.get("name", url)

            if url in checkpoint["processed_urls"]:
                logger.info("  [skip] %s (déjà traité)", name)
                prev = checkpoint["processed_urls"][url]
                if prev.get("slug"):
                    imported_slugs.append(prev["slug"])
                continue

            logger.info("  [%d/%d] %s", i + 1, len(recipes), name)

            if dry_run:
                checkpoint["processed_urls"][url] = {"dry_run": True, "name": name}
                continue

            # 1. Import
            result = import_recipe(url, session)
            slug = result.get("slug") or result.get("recipe_slug")

            if not result.get("success") or not slug:
                logger.warning("    ✗ Import échoué: %s", result.get("error", "?"))
                checkpoint["processed_urls"][url] = {
                    "status": "error",
                    "error": result.get("error", "unknown"),
                    "name": name,
                }
                save_checkpoint(checkpoint)
                if delay_recipe > 0 and i < len(recipes) - 1:
                    time.sleep(delay_recipe)
                continue

            logger.info("    ✓ Importé: slug=%s", slug)
            entry: dict = {"status": "imported", "slug": slug, "name": name}

            # 2. Nutrition
            if not skip_nutrition:
                nutr = enrich_nutrition(slug, session)
                if nutr.get("success") is False:
                    logger.warning("    ⚠ Nutrition: %s", nutr.get("error", "?"))
                    entry["nutrition"] = "error"
                else:
                    logger.info("    ✓ Nutrition enrichie")
                    entry["nutrition"] = "ok"

            imported_slugs.append(slug)
            checkpoint["processed_urls"][url] = entry
            save_checkpoint(checkpoint)

            if delay_recipe > 0 and i < len(recipes) - 1:
                time.sleep(delay_recipe)

    # 3. Coûts batch (une fois par lot)
    if imported_slugs and not skip_costs and not dry_run:
        logger.info("  💰 Calcul des coûts pour %d recettes...", len(imported_slugs))
        with requests.Session() as session:
            cost_result = enrich_costs_batch(imported_slugs, session)
        if cost_result.get("skipped"):
            logger.info("  Coûts: ignorés (BUDGET_API_URL non configuré)")
        elif cost_result.get("success") is False:
            logger.warning("  ⚠ Coûts: %s", cost_result.get("error", "?"))
        else:
            logger.info("  ✓ Coûts calculés")

    return imported_slugs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Import par batch depuis un JSON scrappé Marmiton")
    parser.add_argument("--input", "-i", help="Fichier JSON source (scrape_marmiton_urls.py)")
    parser.add_argument("--resume", action="store_true", help="Reprend depuis le checkpoint existant")
    parser.add_argument(
        "--categories",
        nargs="+",
        help="Catégories à traiter (ex: entree dessert). Défaut: toutes",
    )
    parser.add_argument("--batch-size", type=int, default=10, help="Recettes par lot (défaut: 10)")
    parser.add_argument(
        "--delay-recipe",
        type=float,
        default=3.0,
        help="Délai entre chaque recette en secondes (défaut: 3)",
    )
    parser.add_argument(
        "--delay-batch",
        type=float,
        default=30.0,
        help="Délai entre chaque lot en secondes (défaut: 30)",
    )
    parser.add_argument("--no-nutrition", action="store_true", help="Ne pas enrichir la nutrition")
    parser.add_argument("--no-costs", action="store_true", help="Ne pas calculer les coûts")
    parser.add_argument("--dry-run", action="store_true", help="Simulation sans import réel")
    args = parser.parse_args()

    # Trouver le fichier source
    if args.input:
        input_path = Path(args.input)
    else:
        candidates = sorted(DATA_DIR.glob("marmiton_urls_*.json"), reverse=True)
        if not candidates:
            logger.error("Aucun fichier marmiton_urls_*.json trouvé dans %s", DATA_DIR)
            logger.error("Lancer d'abord: python3 scripts/scrape_marmiton_urls.py")
            raise SystemExit(1)
        input_path = candidates[0]
        logger.info("Fichier source auto-détecté: %s", input_path)

    if not input_path.exists():
        logger.error("Fichier introuvable: %s", input_path)
        raise SystemExit(1)

    scraped = json.loads(input_path.read_text())
    checkpoint = load_checkpoint()

    if not args.resume and checkpoint["processed_urls"]:
        already = len(checkpoint["processed_urls"])
        logger.info("Checkpoint existant: %d recettes déjà traitées (--resume pour continuer)", already)
        confirm = input("Réinitialiser le checkpoint et tout retraiter ? [y/N] ").strip().lower()
        if confirm == "y":
            checkpoint = {"processed_urls": {}, "created_at": datetime.now().isoformat()}
            save_checkpoint(checkpoint)

    # Construire la liste des recettes à traiter
    all_recipes: list[dict] = []
    categories = scraped.get("categories", {})
    selected_cats = args.categories or list(categories.keys())

    for cat_key in selected_cats:
        cat_data = categories.get(cat_key)
        if not cat_data:
            logger.warning("Catégorie '%s' absente du fichier source", cat_key)
            continue
        for recipe in cat_data.get("recipes", []):
            recipe["_category"] = cat_key
            recipe["_mealie_category"] = cat_data.get("mealie_category", cat_key)
            recipe["_course_type"] = cat_data.get("course_type", "main")
            all_recipes.append(recipe)

    total = len(all_recipes)
    pending = [r for r in all_recipes if r["url"] not in checkpoint["processed_urls"]]
    logger.info(
        "Total: %d recettes | Déjà traitées: %d | À traiter: %d",
        total, total - len(pending), len(pending),
    )

    if args.dry_run:
        logger.info("[DRY-RUN] Simulation uniquement — aucun import réel")

    # Découper en lots et traiter
    batch_size = args.batch_size
    batches = [all_recipes[i : i + batch_size] for i in range(0, len(all_recipes), batch_size)]
    total_imported = 0
    total_errors = 0

    for batch_num, batch in enumerate(batches, start=1):
        pending_in_batch = [r for r in batch if r["url"] not in checkpoint["processed_urls"]]
        if not pending_in_batch:
            logger.info("Lot %d/%d : déjà traité, skip", batch_num, len(batches))
            continue

        logger.info(
            "=== Lot %d/%d (%d recettes) ===",
            batch_num, len(batches), len(pending_in_batch),
        )

        slugs = process_batch(
            pending_in_batch,
            checkpoint,
            dry_run=args.dry_run,
            delay_recipe=args.delay_recipe,
            skip_nutrition=args.no_nutrition,
            skip_costs=args.no_costs,
        )
        total_imported += len(slugs)

        errors_in_batch = sum(
            1 for r in pending_in_batch
            if checkpoint["processed_urls"].get(r["url"], {}).get("status") == "error"
        )
        total_errors += errors_in_batch

        logger.info(
            "Lot %d terminé: %d importés, %d erreurs",
            batch_num, len(slugs), errors_in_batch,
        )

        if batch_num < len(batches) and args.delay_batch > 0:
            logger.info("Pause %ds avant le prochain lot...", int(args.delay_batch))
            time.sleep(args.delay_batch)

    # Résumé final
    print("\n=== RÉSUMÉ ===")
    print(f"  Recettes importées : {total_imported}")
    print(f"  Erreurs            : {total_errors}")
    print(f"  Checkpoint         : {CHECKPOINT_FILE}")
    if args.dry_run:
        print("  Mode DRY-RUN — aucun import réel effectué")


if __name__ == "__main__":
    main()
