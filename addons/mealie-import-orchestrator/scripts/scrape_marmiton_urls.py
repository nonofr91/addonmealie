#!/usr/bin/env python3
"""
Scraper d'URLs de recettes Marmiton par catégorie.

Usage:
    python3 scrape_marmiton_urls.py --categories entree plat-principal dessert
    python3 scrape_marmiton_urls.py --categories entree --max-pages 10
    python3 scrape_marmiton_urls.py --categories entree --output /tmp/entrees.json

Sortie : JSON avec liste d'URLs par catégorie, sauvegardé dans data/
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://www.marmiton.org"

# Catégories Marmiton → slug URL + CourseType Mealie correspondant
CATEGORIES = {
    "entree": {
        "url_slug": "entree",
        "mealie_category": "Entrée",
        "course_type": "starter",
    },
    "plat-principal": {
        "url_slug": "plat-principal",
        "mealie_category": "Plat principal",
        "course_type": "main",
    },
    "dessert": {
        "url_slug": "dessert",
        "mealie_category": "Dessert",
        "course_type": "dessert",
    },
    "accompagnement": {
        "url_slug": "accompagnement",
        "mealie_category": "Accompagnement",
        "course_type": "side",
    },
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _extract_urls_from_jsonld(html: str) -> list[dict]:
    """Extrait les recettes depuis le JSON-LD ItemList de la page."""
    import json as _json
    pattern = re.compile(
        r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', re.DOTALL
    )
    recipes = []
    for block in pattern.findall(html):
        try:
            data = _json.loads(block.strip())
            items = data if isinstance(data, list) else [data]
            for item in items:
                if item.get("@type") == "ItemList":
                    for elem in item.get("itemListElement", []):
                        url = elem.get("url", "")
                        if "/recettes/recette_" in url:
                            recipes.append({
                                "url": url,
                                "name": elem.get("name", ""),
                                "image": elem.get("image", ""),
                            })
        except Exception:
            pass
    return recipes


def scrape_category_page(session: requests.Session, url_slug: str, page: int) -> list[dict]:
    """Récupère les recettes sur une page d'une catégorie (JSON-LD ItemList).

    Marmiton utilise un path numérique pour la pagination :
    - Page 1 : /recettes/index/categorie/{slug}/
    - Page N : /recettes/index/categorie/{slug}/{N}
    """
    if page == 1:
        url = f"{BASE_URL}/recettes/index/categorie/{url_slug}/"
    else:
        url = f"{BASE_URL}/recettes/index/categorie/{url_slug}/{page}"

    try:
        resp = session.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return _extract_urls_from_jsonld(resp.text)
    except requests.RequestException as exc:
        logger.warning("Erreur page %d de '%s': %s", page, url_slug, exc)
        return []


def scrape_category(
    url_slug: str,
    max_pages: int = 50,
    delay: float = 1.0,
) -> list[dict]:
    """Scrape toutes les recettes d'une catégorie (URL + nom + image)."""
    all_recipes: list[dict] = []
    seen_urls: set[str] = set()
    consecutive_empty = 0

    with requests.Session() as session:
        for page in range(1, max_pages + 1):
            logger.info("Scraping '%s' page %d/%d...", url_slug, page, max_pages)
            recipes = scrape_category_page(session, url_slug, page)

            new_recipes = [r for r in recipes if r["url"] not in seen_urls]
            if not new_recipes:
                consecutive_empty += 1
                if consecutive_empty >= 2:
                    logger.info(
                        "Fin de catégorie '%s' détectée à la page %d",
                        url_slug,
                        page,
                    )
                    break
            else:
                consecutive_empty = 0
                for r in new_recipes:
                    seen_urls.add(r["url"])
                all_recipes.extend(new_recipes)
                logger.info("  → %d nouvelles recettes (total: %d)", len(new_recipes), len(all_recipes))

            if page < max_pages:
                time.sleep(delay)

    return all_recipes


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape les URLs de recettes Marmiton par catégorie")
    parser.add_argument(
        "--categories",
        nargs="+",
        default=list(CATEGORIES.keys()),
        choices=list(CATEGORIES.keys()),
        help="Catégories à scraper (défaut: toutes)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=50,
        help="Nombre maximum de pages par catégorie (défaut: 50, ~1500 recettes)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Délai entre les requêtes en secondes (défaut: 1.0)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Fichier de sortie JSON (défaut: data/marmiton_urls_YYYY-MM-DD.json)",
    )
    args = parser.parse_args()

    results: dict = {
        "scraped_at": datetime.now().isoformat(),
        "categories": {},
        "total_urls": 0,
    }

    for cat_key in args.categories:
        cat_info = CATEGORIES[cat_key]
        logger.info("=== Catégorie : %s ===", cat_key)
        recipes = scrape_category(
            url_slug=cat_info["url_slug"],
            max_pages=args.max_pages,
            delay=args.delay,
        )
        results["categories"][cat_key] = {
            "url_slug": cat_info["url_slug"],
            "mealie_category": cat_info["mealie_category"],
            "course_type": cat_info["course_type"],
            "count": len(recipes),
            "recipes": recipes,
        }
        results["total_urls"] += len(recipes)
        logger.info("✓ %s: %d recettes scrapées", cat_key, len(recipes))

    # Déterminer le fichier de sortie
    if args.output:
        output_path = Path(args.output)
    else:
        data_dir = Path(__file__).parent.parent / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_path = data_dir / f"marmiton_urls_{date_str}.json"

    output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    logger.info("✓ Résultats sauvegardés dans %s (%d URLs total)", output_path, results["total_urls"])

    # Résumé
    print("\n=== RÉSUMÉ ===")
    for cat_key, cat_data in results["categories"].items():
        print(f"  {cat_key}: {cat_data['count']} recettes")
    print(f"  TOTAL: {results['total_urls']} URLs")
    print(f"  Fichier: {output_path}")


if __name__ == "__main__":
    main()
