"""
FastAPI pour le service DriveCarrefour.
Fournit des endpoints pour optimiser les listes de courses Mealie avec Carrefour.
"""

from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
import httpx
import yaml
from pathlib import Path

from mappers.mealie_to_carrefour import MealieToCarrefourMapper

# Chargement de la configuration
CONFIG_PATH = Path(__file__).parent.parent / "config" / "settings.yaml"
with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

# Initialisation de l'application
app = FastAPI(
    title=config["api"]["title"],
    description=config["api"]["description"],
    version=config["api"]["version"],
    debug=config["api"]["debug"]
)

# CORS Middleware (pour permettre les requêtes depuis Mealie ou ton frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Client HTTP pour les requêtes vers Mealie
mealie_client = httpx.AsyncClient(
    base_url=config["mealie"]["api_url"],
    timeout=30.0
)


@app.on_event("startup")
async def startup_event():
    """Initialisation au démarrage."""
    print(f"DriveCarrefour API démarrée sur {config['api']['host']}:{config['api']['port']}")


@app.on_event("shutdown")
async def shutdown_event():
    """Nettoyage à l'arrêt."""
    await mealie_client.aclose()


# ==================== ENDPOINTS PRINCIPAUX ====================

@app.get("/", tags=["Health"])
async def root():
    """Endpoint de santé."""
    return {
        "service": "DriveCarrefour",
        "version": config["api"]["version"],
        "status": "OK",
        "endpoints": {
            "/optimize": "Optimise une liste de courses",
            "/search": "Recherche un produit sur Carrefour",
            "/health": "Vérifie l'état du service"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Vérifie l'état du service et des dépendances."""
    try:
        # Test de la connexion à Mealie
        mealie_health = await mealie_client.get("/health")
        mealie_status = mealie_health.status_code == 200
    except Exception:
        mealie_status = False
    
    return {
        "status": "OK",
        "dependencies": {
            "mealie": "OK" if mealie_status else "UNREACHABLE"
        }
    }


@app.get("/search/{query}", tags=["Carrefour"])
async def search_carrefour(
    query: str,
    max_pages: int = Query(1, ge=1, le=5, description="Nombre de pages à scraper"),
    use_cache: bool = Query(True, description="Utiliser le cache")
) -> List[Dict]:
    """
    Recherche des produits sur Carrefour.
    
    **Exemple** :
    ```bash
    curl http://localhost:8000/search/oeufs
    ```
    """
    async with MealieToCarrefourMapper() as mapper:
        try:
            # Désactive le cache si demandé
            if not use_cache:
                mapper.scraper.cache_enabled = False
            
            products = await mapper.scraper.search_products(query, max_pages=max_pages)
            return products
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/optimize", tags=["Shopping List"])
async def optimize_shopping_list(
    shopping_list: List[Dict],
    use_cache: bool = Query(True, description="Utiliser le cache"),
    preferred_brands: Optional[List[str]] = Query(None, description="Marques préférées"),
    excluded_brands: Optional[List[str]] = Query(None, description="Marques à exclure")
) -> Dict:
    """
    Optimise une liste de courses Mealie avec les produits Carrefour.
    
    **Requête** :
    ```json
    {
      "items": [
        {"name": "Œufs", "quantity": 6, "unit": "pièce"},
        {"name": "Farine T55", "quantity": 500, "unit": "g"},
        {"name": "Lait entier", "quantity": 1, "unit": "L"}
      ]
    }
    ```
    
    **Réponse** :
    ```json
    {
      "total_cost": 15.99,
      "items": [
        {
          "ingredient": "Œufs",
          "product_name": "Œufs de poules élevées en plein air - 6",
          "product_price": 2.99,
          "product_url": "https://www.carrefour.fr/...",
          "quantity_to_buy": 1,
          "unit_to_buy": "barquette"
        }
      ]
    }
    ```
    """
    async with MealieToCarrefourMapper() as mapper:
        try:
            # Désactive le cache si demandé
            if not use_cache:
                mapper.scraper.cache_enabled = False
            
            # Applique les préférences utilisateur
            if preferred_brands:
                # TODO: Implémenter le filtrage par marques préférées
                pass
            if excluded_brands:
                # TODO: Implémenter l'exclusion des marques
                pass
            
            results = await mapper.map_shopping_list(shopping_list)
            
            # Calcul du coût total
            total_cost = sum(
                r.get("total_cost", 0) or 0 for r in results if "error" not in r
            )
            
            return {
                "status": "success",
                "total_cost": round(total_cost, 2),
                "currency": "€",
                "items": results
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/mealie/lists", tags=["Mealie"])
async def get_mealie_shopping_lists(
    group_id: str = Query("1", description="ID du groupe Mealie"),
    api_token: str = Header(..., description="Token API Mealie")
) -> List[Dict]:
    """
    Récupère la liste des listes de courses depuis Mealie.
    
    **Headers** :
    ```
    Authorization: Bearer TON_TOKEN_MEALIE
    ```
    """
    try:
        headers = {"Authorization": f"Bearer {api_token}"}
        response = await mealie_client.get(
            f"/groups/{group_id}/shopping/lists",
            headers=headers
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Erreur Mealie: {response.text}"
            )
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mealie/lists/{list_id}/items", tags=["Mealie"])
async def get_mealie_shopping_list_items(
    list_id: str,
    group_id: str = Query("1", description="ID du groupe Mealie"),
    api_token: str = Header(..., description="Token API Mealie")
) -> List[Dict]:
    """
    Récupère les éléments d'une liste de courses Mealie.
    
    **Headers** :
    ```
    Authorization: Bearer TON_TOKEN_MEALIE
    ```
    """
    try:
        headers = {"Authorization": f"Bearer {api_token}"}
        response = await mealie_client.get(
            f"/groups/{group_id}/shopping/lists/{list_id}/items",
            headers=headers
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Erreur Mealie: {response.text}"
            )
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mealie/lists/{list_id}/optimize", tags=["Mealie"])
async def optimize_mealie_shopping_list(
    list_id: str,
    group_id: str = Query("1", description="ID du groupe Mealie"),
    api_token: str = Header(..., description="Token API Mealie"),
    use_cache: bool = Query(True, description="Utiliser le cache")
) -> Dict:
    """
    Optimise une liste de courses Mealie existante via son ID.
    
    **Headers** :
    ```
    Authorization: Bearer TON_TOKEN_MEALIE
    ```
    
    **Réponse** : Même format que /optimize
    """
    # 1. Récupérer la liste depuis Mealie
    try:
        headers = {"Authorization": f"Bearer {api_token}"}
        response = await mealie_client.get(
            f"/groups/{group_id}/shopping/lists/{list_id}/items",
            headers=headers
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Erreur Mealie: {response.text}"
            )
        shopping_list = response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération de la liste Mealie: {e}")
    
    # 2. Optimiser avec Carrefour
    async with MealieToCarrefourMapper() as mapper:
        try:
            if not use_cache:
                mapper.scraper.cache_enabled = False
            
            results = await mapper.map_shopping_list(shopping_list)
            total_cost = sum(
                r.get("total_cost", 0) or 0 for r in results if "error" not in r
            )
            
            return {
                "status": "success",
                "mealie_list_id": list_id,
                "total_cost": round(total_cost, 2),
                "currency": "€",
                "items": results
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


# ==================== ENDPOINTS UTILITAIRES ====================

@app.get("/synonyms/{ingredient}", tags=["Utils"])
async def get_synonyms(ingredient: str) -> Dict:
    """
    Récupère les synonymes pour un ingrédient.
    """
    async with MealieToCarrefourMapper() as mapper:
        synonyms = mapper._get_synonyms(ingredient)
        return {
            "ingredient": ingredient,
            "synonyms": synonyms
        }


@app.get("/units/{unit}", tags=["Utils"])
async def get_compatible_units(unit: str) -> Dict:
    """
    Récupère les unités compatibles pour une unité donnée.
    """
    async with MealieToCarrefourMapper() as mapper:
        compatible_units = mapper.UNIT_CONVERSION.get(unit, [])
        return {
            "unit": unit,
            "compatible_units": compatible_units
        }


# ==================== POUR TESTS LOCAUX ====================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "shopping_api:app",
        host=config["api"]["host"],
        port=config["api"]["port"],
        reload=config["api"]["debug"]
    )
