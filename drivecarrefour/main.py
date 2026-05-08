#!/usr/bin/env python3
"""
Point d'entrée principal pour le service DriveCarrefour.

Ce script permet de:
1. Lancer l'API FastAPI
2. Exécuter des commandes CLI pour le scraping
3. Tester le service

Usage:
    # Lancer l'API
    python main.py api
    
    # Tester le scraper
    python main.py test-scraper --query "oeufs"
    
    # Optimiser une liste de courses
    python main.py optimize --input "[{'name': 'Œufs', 'quantity': 6, 'unit': 'pièce'}]"
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Ajout du répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent))

from api.shopping_api import app
from scrapers.carrefour_scraper import CarrefourScraper
from mappers.mealie_to_carrefour import MealieToCarrefourMapper
import uvicorn


def parse_args():
    """Parse les arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(
        description="DriveCarrefour - Service d'optimisation des listes de courses avec Carrefour"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commande à exécuter")
    
    # Commande API
    api_parser = subparsers.add_parser("api", help="Lance l'API FastAPI")
    api_parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="Adresse hôte (default: 0.0.0.0)"
    )
    api_parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port (default: 8000)"
    )
    api_parser.add_argument(
        "--reload", 
        action="store_true", 
        help="Activer le rechargement automatique (pour le développement)"
    )
    
    # Commande test-scraper
    scraper_parser = subparsers.add_parser("test-scraper", help="Teste le scraper Carrefour")
    scraper_parser.add_argument(
        "--query", 
        default="oeufs", 
        help="Terme de recherche (default: oeufs)"
    )
    scraper_parser.add_argument(
        "--no-cache", 
        action="store_true", 
        help="Désactiver le cache"
    )
    scraper_parser.add_argument(
        "--limit", 
        type=int, 
        default=5, 
        help="Nombre maximal de produits à afficher (default: 5)"
    )
    
    # Commande optimize
    optimize_parser = subparsers.add_parser("optimize", help="Optimise une liste de courses")
    optimize_parser.add_argument(
        "--input", 
        default='[{"name": "Œufs", "quantity": 6, "unit": "pièce"}, {"name": "Farine T55", "quantity": 500, "unit": "g"}]',
        help="Liste de courses au format JSON (default: exemple avec œufs et farine)"
    )
    optimize_parser.add_argument(
        "--no-cache", 
        action="store_true", 
        help="Désactiver le cache"
    )
    
    # Commande health
    subparsers.add_parser("health", help="Vérifie l'état du service")
    
    # Commande search-synonyms
    synonyms_parser = subparsers.add_parser("search-synonyms", help="Recherche les synonymes d'un ingrédient")
    synonyms_parser.add_argument(
        "ingredient", 
        help="Nom de l'ingrédient"
    )
    
    return parser.parse_args()


async def run_api(host: str, port: int, reload: bool):
    """Lance l'API FastAPI."""
    print(f"Démarrage de l'API DriveCarrefour sur {host}:{port}")
    print(f"Documentation disponible à: http://{host}:{port}/docs")
    
    await uvicorn.run(
        "api.shopping_api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


async def test_scraper(query: str, no_cache: bool, limit: int):
    """Teste le scraper Carrefour."""
    print(f"Recherche de produits pour: '{query}'")
    
    async with CarrefourScraper(cache_enabled=not no_cache) as scraper:
        products = await scraper.search_products(query)
        
        print(f"\nTrouvé {len(products)} produits:\n")
        
        for i, product in enumerate(products[:limit], 1):
            print(f"{i}. {product.get('name', 'N/A')}")
            print(f"   Marque: {product.get('brand', 'N/A')}")
            print(f"   Prix: {product.get('price', 'N/A')}€")
            print(f"   Prix/unité: {product.get('price_per_unit', 'N/A')}€")
            print(f"   Poids: {product.get('weight', 'N/A')}")
            print(f"   Unité: {product.get('unit', 'N/A')}")
            print(f"   Conditionnement: {product.get('packaging', 'N/A')}")
            print(f"   Disponible: {'Oui' if product.get('availability') else 'Non'}")
            print(f"   URL: {product.get('url', 'N/A')}")
            print()


async def optimize_shopping_list(input_json: str, no_cache: bool):
    """Optimise une liste de courses."""
    try:
        shopping_list = json.loads(input_json)
    except json.JSONDecodeError as e:
        print(f"Erreur: JSON invalide - {e}")
        return
    
    print(f"Optimisation de la liste de courses:")
    print(json.dumps(shopping_list, indent=2, ensure_ascii=False))
    print()
    
    async with MealieToCarrefourMapper() as mapper:
        if no_cache:
            mapper.scraper.cache_enabled = False
        
        results = await mapper.map_shopping_list(shopping_list)
        
        print("Résultats optimisés:\n")
        total_cost = 0.0
        
        for i, result in enumerate(results, 1):
            if "error" in result:
                print(f"{i}. ❌ {result.get('ingredient', 'N/A')}: {result.get('error', 'Erreur inconnue')}")
                continue
            
            print(f"{i}. ✅ {result.get('ingredient', 'N/A')} ({result.get('quantity_needed', 0)} {result.get('unit_needed', '')})")
            print(f"   → Produit: {result.get('product_name', 'N/A')}")
            print(f"   → Marque: {result.get('product_brand', 'N/A')}")
            print(f"   → Prix: {result.get('product_price', 0)}€")
            print(f"   → Prix/unité: {result.get('product_price_per_unit', 0)}€")
            print(f"   → Quantité à acheter: {result.get('quantity_to_buy', 0)} {result.get('unit_to_buy', '')}")
            print(f"   → Coût total: {result.get('total_cost', 0)}€")
            print(f"   → URL: {result.get('product_url', 'N/A')}")
            print(f"   → Pourquoi: {result.get('why', 'N/A')}")
            print()
            
            total_cost += result.get('total_cost', 0) or 0
        
        print(f"Coût total estimé: {total_cost:.2f}€")


async def check_health():
    """Vérifie l'état du service."""
    print("Vérification de l'état du service DriveCarrefour...")
    
    # Test du scraper
    try:
        async with CarrefourScraper(cache_enabled=False) as scraper:
            html = await scraper._fetch("https://www.carrefour.fr")
            print("✅ Connexion à Carrefour.fr: OK")
    except Exception as e:
        print(f"❌ Connexion à Carrefour.fr: ÉCHEC - {e}")
    
    # Test du mapper
    try:
        async with MealieToCarrefourMapper() as mapper:
            synonyms = mapper._get_synonyms("oeufs")
            print(f"✅ Mapper: OK (synonymes pour 'oeufs': {synonyms})")
    except Exception as e:
        print(f"❌ Mapper: ÉCHEC - {e}")
    
    print("\nToutes les vérifications sont terminées.")


async def search_synonyms(ingredient: str):
    """Recherche les synonymes d'un ingrédient."""
    async with MealieToCarrefourMapper() as mapper:
        synonyms = mapper._get_synonyms(ingredient)
        
        print(f"Synonymes pour '{ingredient}':")
        for i, synonym in enumerate(synonyms, 1):
            print(f"  {i}. {synonym}")


async def main():
    """Point d'entrée principal."""
    args = parse_args()
    
    if args.command is None:
        print("Aucune commande spécifiée. Utilisez --help pour voir les options.")
        return
    
    if args.command == "api":
        await run_api(args.host, args.port, args.reload)
    
    elif args.command == "test-scraper":
        await test_scraper(args.query, args.no_cache, args.limit)
    
    elif args.command == "optimize":
        await optimize_shopping_list(args.input, args.no_cache)
    
    elif args.command == "health":
        await check_health()
    
    elif args.command == "search-synonyms":
        await search_synonyms(args.ingredient)
    
    else:
        print(f"Commande inconnue: {args.command}")
        print("Utilisez --help pour voir les options disponibles.")


if __name__ == "__main__":
    asyncio.run(main())
