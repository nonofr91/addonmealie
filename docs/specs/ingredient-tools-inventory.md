# Inventory des outils d'ingrédients et d'import

## Source de vérité canonique

- **Serveur MCP canonique** : `mealie-mcp-server/`
- **Workflow canonique** : `addons/mealie-import-orchestrator/` + `mealie-workflow/`
- **Wrapper local** : `mealie-workflow/mcp_auth_wrapper.py`

## État actuel du MCP canonique

### Tools exposés (44 total)
- **recipes** : 12
- **categories** : 7
- **tags** : 7
- **shopping lists** : 14
- **mealplan** : 4

### Mixins backend
- `RecipeMixin`
- `CategoriesMixin`
- `TagsMixin`
- `ShoppingListMixin`
- `MealplanMixin`
- `UserMixin`
- `GroupMixin`

## Capacités historiques mentionnées mais non reprises

### Tools ingrédients (absents du serveur canonique)

Ces capacités sont documentées dans :
- `.windsurf/workflows/ingredient-manager.md`
- `GUIDE_COMPLET.md`
- `docs/temp/rapport_test_10_recettes.md`

Liste des tools manquants :

1. **`validate_ingredients_structure`** - Valider la structure des ingrédients
2. **`intelligent_ingredient_structurer`** - Analyser les ingrédients avec IA
3. **`complete_ingredient_migration`** - Migration complète avec création d'éléments
4. **`correct_existing_foods`** - Corriger les noms d'aliments existants
5. **`explore_foods`** - Explorer les aliments avec pagination
6. **`search_foods_by_name`** - Rechercher des aliments par nom
7. **`get_foods_list`** - Lister tous les aliments disponibles
8. **`get_units_list`** - Lister toutes les unités de mesure
9. **`create_food_ingredient`** - Créer un nouvel aliment
10. **`create_measurement_unit`** - Créer une nouvelle unité
11. **`enable_recipe_automation`** - Activer l'automatisation d'une recette

### Tools import avancé (absents du serveur canonique)

Ces capacités sont documentées dans :
- `README_MCP_MEALIE.md`
- `GUIDE_COMPLET.md`

Liste des tools manquants :

1. **`scrape_recipe`** - Importe une recette depuis une URL (différent de create_recipe)
2. **`import_ia_bulk`** - Importe en masse des recettes françaises
3. **`get_import_ia_status`** - Affiche le statut du cookbook Import IA
4. **`organize_import_ia`** - Organise les recettes dans le cookbook Import IA
5. **`create_recipe_from_url`** - Import d'une recette spécifique depuis une URL

## Capacités bien conservées

### Import de recette (workflow canonique)

**Fichier** : `mealie-workflow/src/importing/mealie_importer_mcp.py`
**Wrapper** : `mealie-workflow/mcp_auth_wrapper.py`

Helpers rechargés par le wrapper :
- `mcp3_validate_recipe.py`
- `mcp3_verify_import.py`
- `mcp3_import_batch.py`
- `mcp3_check_recipe_quality.py`
- `mcp3_cleanup_duplicates.py`
- `mcp3_fix_invalid_recipes.py`

Fonctions CRUD de base :
- `mcp3_list_recipes`
- `mcp3_get_recipe_details`
- `mcp3_create_recipe`
- `mcp3_update_recipe`
- `mcp3_delete_recipe`

### Scraper (workflow métier)

**Fichier** : `mealie-workflow/src/scraping/recipe_scraper_mcp.py`
**Skill** : `mealie-workflow/skills/recipe_scraper_skill.py`

Fonctions :
- `scrape_recipes(sources)`
- `scrape_recipe(url)`
- `list_sources()`
- `get_scraping_info()`

## Plan de restauration canonique

### Phase 1 : Backend Foods/Units (serveur MCP canonique)

**Fichiers à créer/modifier dans `mealie-mcp-server/src/mealie/`** :

1. **Créer `foods.py`** avec `FoodsMixin`
   - `get_foods()`
   - `search_foods_by_name()`
   - `get_food()`
   - `create_food()`

2. **Créer `units.py`** avec `UnitsMixin`
   - `get_units()`
   - `get_unit()`
   - `create_unit()`

3. **Modifier `__init__.py`** pour inclure les nouveaux mixins

### Phase 2 : Tools Ingredients (serveur MCP canonique)

**Fichier à créer dans `mealie-mcp-server/src/tools/`** :

1. **Créer `ingredients_tools.py`**
   - Enregistrer les tools foods/units bas niveau
   - `get_foods_list`
   - `search_foods_by_name`
   - `get_units_list`
   - `create_food_ingredient`
   - `create_measurement_unit`

2. **Modifier `__init__.py`** pour enregistrer `ingredients_tools`

### Phase 3 : Workflow métier avancé (mealie-workflow)

**Fichiers à créer/modifier dans `mealie-workflow/`** :

Ces capacités composées restent côté workflow métier, pas dans le MCP bas niveau :

1. **Créer ou adapter des skills** pour :
   - `validate_ingredients_structure`
   - `intelligent_ingredient_structurer`
   - `complete_ingredient_migration`
   - `correct_existing_foods`

2. **Intégrer ces skills** dans le workflow orchestrator si nécessaire

### Phase 4 : Import IA avancé (optionnel, à discuter)

Ces outils sont plus spécifiques et peuvent être gardés comme :
- workflow métier spécialisé
- ou outils MCP dédiés si besoin d'exposition directe

Outils à évaluer :
- `import_ia_bulk`
- `get_import_ia_status`
- `organize_import_ia`
- `scrape_recipe` (différent de create_recipe)

## Priorité de restauration

### Critique (Phase 1 + 2)
- **Foods/Units backend** + **tools bas niveau**
- Essentiel pour toute logique d'optimisation d'ingrédients

### Important (Phase 3)
- **Workflow métier d'optimisation d'ingrédients**
- Capacités composées utilisant les tools bas niveau

### À évaluer (Phase 4)
- **Import IA avancé**
- Dépend des besoins réels du projet

## Statut actuel

- **Inventory** : Complet
- **Phase 1** : Non démarrée
- **Phase 2** : Non démarrée
- **Phase 3** : Non démarrée
- **Phase 4** : À évaluer
