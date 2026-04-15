# Décision : Two-step POST + PATCH pour la création de recettes Mealie

## Date
2026-04-15

## Contexte

L'API `POST /api/recipes` de Mealie v3.x ne stocke pas les données complètes d'une recette.
Elle accepte uniquement `{"name": "..."}` et retourne un slug string.
Toute tentative d'envoyer un payload complet (ingrédients, instructions, etc.) est ignorée.

## Problème

- `POST /api/recipes` avec payload complet → seul le nom est stocké
- `PUT /api/recipes/{slug}` → retourne `400 "Recipe already exists"` si le slug existe
- `PATCH /api/recipes/{slug}` avec `name`/`slug` → retourne `400 "Recipe already exists"`

## Décision

Implémenter un workflow en 4 étapes dans `mcp3_create_recipe` (`mcp_auth_wrapper.py`) :

```
1. POST /api/recipes         → {"name": "Nom recette"} → slug
2. GET /api/recipes/{slug}   → vrai nom (peut avoir suffixe -2, -3...)
3. PATCH /api/recipes/{slug} → payload complet sans name/slug
4. POST /api/recipes/{slug}/image → {"url": "https://..."} → scraping image
```

## Contraintes respectées

- `PATCH` : ne pas inclure `name` ni `slug` dans le payload (cause 400)
- `image` : toujours `null` dans le PATCH, géré séparément via l'endpoint dédié
- `recipeCategory` / `tags` : objets `{id, name, slug}` via `organizers/categories` et `organizers/tags`
- `recipeIngredient.unit` / `.food` : objets `{id, name}` via `_get_or_create_food/_unit`

## Résolution foods/units

Pour garantir la standardisation des ingrédients entre recettes :

```python
_build_mealie_cache(api_url, headers)
# → {nom_lower: objet_mealie} pour foods ET units

_get_or_create_food(api_url, headers, food_name, cache)
# 1. clean: supprime prépositions FR (de, d', des, du, l', la, le, les)
# 2. lookup cache case-insensitive
# 3. si absent → POST /api/foods {"name": food_name}

_get_or_create_unit(api_url, headers, unit_name, cache)
# 1. lookup cache (name + abbreviation)
# 2. si absent → POST /api/units {"name": unit_name}
```

## Endpoints Mealie v3 utilisés

| Méthode | Endpoint | Usage |
|---------|----------|-------|
| POST | `/api/recipes` | Créer recette (nom only) |
| GET | `/api/recipes/{slug}` | Récupérer vrai nom assigné |
| PATCH | `/api/recipes/{slug}` | Peupler ingrédients, instructions, meta |
| POST | `/api/recipes/{slug}/image` | Scraper image depuis URL |
| GET | `/api/organizers/categories?perPage=200` | Lister catégories |
| POST | `/api/organizers/categories` | Créer catégorie |
| GET | `/api/organizers/tags?perPage=200` | Lister tags |
| POST | `/api/organizers/tags` | Créer tag |
| GET | `/api/foods?perPage=500` | Cache foods |
| POST | `/api/foods` | Créer food |
| GET | `/api/units?perPage=500` | Cache units |
| POST | `/api/units` | Créer unit |

## Fichiers modifiés

- `mealie-workflow/mcp_auth_wrapper.py` : `mcp3_create_recipe` + helpers
- `mealie-workflow/src/importing/mealie_importer_mcp.py` : restauration unit/food/quantity
- `packages/mealie-dev-stack/docker-compose.yml` : migration vers v3.15.1

## Statut

✅ Implémenté et validé sur Mealie v3.15.1 local
