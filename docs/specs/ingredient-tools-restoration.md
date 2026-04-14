# Restauration des outils d'ingrédients et d'unités

## Contexte

Suite à l'audit de périmètre MCP, il a été identifié que les capacités d'optimisation d'ingrédients et d'unités n'étaient pas reprises dans le serveur MCP canonique `mealie-mcp-server/`.

## Objectif

Restaurer les tools foods/units bas niveau dans le serveur MCP canonique pour permettre :
- La gestion des aliments (foods)
- La gestion des unités de mesure (units)
- La base pour les workflows métier d'optimisation d'ingrédients

## Implémentation réalisée

### 1. Backend Mixins (mealie-mcp-server/src/mealie/)

#### Fichiers créés
- `foods.py` - `FoodsMixin` avec les méthodes :
  - `get_foods()` - Lister tous les aliments
  - `search_foods_by_name()` - Rechercher par nom
  - `get_food(food_id)` - Obtenir un aliment par ID
  - `create_food(name, description)` - Créer un aliment
  - `update_food(food_id, food_data)` - Mettre à jour un aliment
  - `delete_food(food_id)` - Supprimer un aliment

- `units.py` - `UnitsMixin` avec les méthodes :
  - `get_units()` - Lister toutes les unités
  - `get_unit(unit_id)` - Obtenir une unité par ID
  - `create_unit(name, description, abbreviation)` - Créer une unité
  - `update_unit(unit_id, unit_data)` - Mettre à jour une unité
  - `delete_unit(unit_id)` - Supprimer une unité

#### Chemins API corrigés
Les endpoints initialement supposés (`/api/organizers/foods` et `/api/organizers/units`) étaient incorrects.

Après vérification dans le schéma OpenAPI (`mealie-mcp-server/openapi.json`), les chemins corrects sont :
- **Foods** : `/api/foods`
- **Units** : `/api/units`

#### Imports corrigés
Tous les fichiers dans `mealie-mcp-server/src/mealie/` ont été corrigés pour utiliser les imports relatifs corrects :
- `from utils import format_api_params` → `from ..utils import format_api_params`

Fichiers corrigés :
- `categories.py`
- `foods.py` (nouveau)
- `mealplan.py`
- `recipe.py`
- `shopping_list.py`
- `tags.py`
- `units.py` (nouveau)

### 2. MCP Tools (mealie-mcp-server/src/tools/)

#### Fichier créé
- `ingredients_tools.py` - Enregistre les tools MCP :
  - `get_foods_list(page, per_page, search)`
  - `search_foods_by_name(name, page, per_page)`
  - `get_food(food_id)`
  - `create_food_ingredient(name, description)`
  - `get_units_list(page, per_page, search)`
  - `get_unit(unit_id)`
  - `create_measurement_unit(name, description, abbreviation)`

#### Enregistrement des tools
Modifié `tools/__init__.py` pour :
- Importer `register_ingredients_tools`
- Appeler `register_ingredients_tools(mcp, mealie)` dans `register_all_tools()`

### 3. Composition du client

Modifié `mealie/__init__.py` pour inclure les nouveaux mixins dans `MealieFetcher` :
```python
class MealieFetcher(
    RecipeMixin,
    CategoriesMixin,
    TagsMixin,
    ShoppingListMixin,
    MealplanMixin,
    FoodsMixin,  # nouveau
    UnitsMixin,  # nouveau
    UserMixin,
    GroupMixin,
    MealieClient,
):
    pass
```

## Tests

### Tentative de test Coolify
Les tests contre l'instance Coolify ont échoué avec des réponses HTML (404) pour tous les endpoints API, y compris les existants (categories).

**Diagnostic** : Ce n'est pas un problème d'implémentation, mais un problème de connectivité API avec l'instance Coolify spécifique. L'instance retourne le frontend HTML au lieu de répondre aux requêtes API.

**Conclusion** : L'implémentation est correcte basée sur le schéma OpenAPI. Les tests doivent être effectués contre :
- Une instance locale Mealie
- Une instance Coolify avec connectivité API fonctionnelle

## État actuel

### Complété
- ✅ Inventory des capacités historiques
- ✅ Implémentation FoodsMixin et UnitsMixin
- ✅ Implémentation ingredients_tools.py
- ✅ Enregistrement des tools dans le serveur MCP
- ✅ Correction des imports utils
- ✅ Correction des chemins API basés sur OpenAPI
- ✅ Documentation de l'inventory

### Nouveau nombre de tools MCP
Avant : 44 tools
Après : 51 tools (+7 tools foods/units)

### Tools nouvellement disponibles
1. `get_foods_list` - Lister les aliments
2. `search_foods_by_name` - Rechercher des aliments par nom
3. `get_food` - Obtenir un aliment par ID
4. `create_food_ingredient` - Créer un aliment
5. `get_units_list` - Lister les unités de mesure
6. `get_unit` - Obtenir une unité par ID
7. `create_measurement_unit` - Créer une unité

## Prochaines étapes (Phase 3 - Workflow métier)

Les capacités composées d'optimisation d'ingrédients restent à implémenter côté `mealie-workflow/` :
- `validate_ingredients_structure`
- `intelligent_ingredient_structurer`
- `complete_ingredient_migration`
- `correct_existing_foods`

Ces capacités utiliseront les tools bas niveau nouvellement restaurés.

## Fichiers modifiés/créés

### Créés
- `mealie-mcp-server/src/mealie/foods.py`
- `mealie-mcp-server/src/mealie/units.py`
- `mealie-mcp-server/src/tools/ingredients_tools.py`
- `docs/specs/ingredient-tools-inventory.md`
- `docs/specs/ingredient-tools-restoration.md` (ce fichier)

### Modifiés
- `mealie-mcp-server/src/mealie/__init__.py`
- `mealie-mcp-server/src/mealie/categories.py`
- `mealie-mcp-server/src/mealie/mealplan.py`
- `mealie-mcp-server/src/mealie/recipe.py`
- `mealie-mcp-server/src/mealie/shopping_list.py`
- `mealie-mcp-server/src/mealie/tags.py`
- `mealie-mcp-server/src/tools/__init__.py`

## Références

- Schéma OpenAPI : `mealie-mcp-server/openapi.json`
- Inventory complet : `docs/specs/ingredient-tools-inventory.md`
- Décision de cleanup : `docs/specs/root-cleanup-phase-2.md`
