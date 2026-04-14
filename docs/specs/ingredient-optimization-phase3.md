# Phase 3 : Implémentation des capacités composées d'optimisation d'ingrédients

## Contexte

Après avoir restauré les tools bas niveau foods/units dans le serveur MCP canonique (Phase 2), cette phase implémente les capacités métier composées qui utilisent ces tools bas niveau.

## Objectif

Implémenter les capacités d'optimisation d'ingrédients dans `mealie-workflow/` sous forme de skill réutilisable, intégré au workflow orchestrator.

## Capacités implémentées

### 1. validate_ingredients_structure
Valide la structure des ingrédients d'une recette.

**Fonctionnalités** :
- Vérifie le format des ingrédients (texte vs structuré)
- Détecte les champs manquants dans les ingrédients structurés
- Identifie les types invalides
- Génère des avertissements pour les formats texte simples

**Signature** :
```python
validate_ingredients_structure(recipe_data: Dict) -> Dict
```

**Retour** :
```python
{
    "success": bool,
    "valid": bool,
    "total_ingredients": int,
    "issues": List[Dict],
    "warnings": List[Dict],
    "message": str
}
```

### 2. intelligent_ingredient_structurer
Analyse et structure les ingrédients avec IA.

**Fonctionnalités** :
- Parse les ingrédients texte en format structuré
- Améliore les ingrédients déjà structurés
- Normalise la structure des ingrédients
- Prépare les données pour l'optimisation avancée

**Signature** :
```python
intelligent_ingredient_structurer(recipe_data: Dict) -> Dict
```

**Retour** :
```python
{
    "success": bool,
    "total_ingredients": int,
    "structured_ingredients": List[Dict],
    "original_count": int,
    "message": str
}
```

### 3. complete_ingredient_migration
Migre complètement les ingrédients avec création d'éléments.

**Fonctionnalités** :
- Planifie la création d'aliments via MCP tools
- Planifie la création d'unités via MCP tools
- Prépare les données pour la migration
- Utilisera les tools `create_food_ingredient` et `create_measurement_unit`

**Signature** :
```python
complete_ingredient_migration(foods_data: List[Dict], units_data: List[Dict]) -> Dict
```

**Retour** :
```python
{
    "success": bool,
    "foods_to_create": int,
    "units_to_create": int,
    "foods": List[Dict],
    "units": List[Dict],
    "message": str
}
```

### 4. correct_existing_foods
Corrige les noms d'aliments existants.

**Fonctionnalités** :
- Applique des corrections en masse sur les aliments
- Valide les corrections avant application
- Suit le statut de chaque correction
- Utilisera les tools foods MCP pour l'application

**Signature** :
```python
correct_existing_foods(corrections: List[Dict]) -> Dict
```

**Retour** :
```python
{
    "success": bool,
    "total_corrections": int,
    "applied_corrections": int,
    "failed_corrections": int,
    "corrections": List[Dict],
    "message": str
}
```

## Implémentation

### Fichier créé
`mealie-workflow/skills/ingredient_optimizer_skill.py`

**Structure** :
- Classe `IngredientOptimizerSkill` avec les 4 méthodes principales
- Fonctions wrapper pour usage direct MCP
- Méthodes privées pour le parsing et l'amélioration
- Test unitaire en `__main__`

### Intégration workflow orchestrator

**Fichier modifié** : `mealie-workflow/workflow_orchestrator.py`

**Modifications** :
- Import de `IngredientOptimizerSkill`
- Instance `self.ingredient_optimizer` dans `__init__`
- Disponible pour usage dans les workflows personnalisés

## Utilisation

### Usage direct via skill

```python
from skills.ingredient_optimizer_skill import validate_ingredients, structure_ingredients

# Validation
validation = validate_ingredients(recipe_data)

# Structuration
structured = structure_ingredients(recipe_data)
```

### Usage via orchestrator

```python
from workflow_orchestrator import MealieWorkflowOrchestrator

orchestrator = MealieWorkflowOrchestrator()

# Accès au skill d'optimisation
validation = orchestrator.ingredient_optimizer.validate_ingredients_structure(recipe_data)
structured = orchestrator.ingredient_optimizer.intelligent_ingredient_structurer(recipe_data)
```

## État actuel

### Complété
- ✅ Implémentation des 4 capacités composées
- ✅ Intégration dans le workflow orchestrator
- ✅ Documentation de l'implémentation

### À améliorer
- **Parsing IA** : L'implémentation actuelle du parsing d'ingrédients texte est basique. Une intégration avec un provider IA permettrait une structuration plus intelligente.
- **Intégration MCP réelle** : Les fonctions `complete_ingredient_migration` et `correct_existing_foods` génèrent actuellement des plans. Elles doivent être connectées aux tools MCP restaurés (`create_food_ingredient`, `create_measurement_unit`, etc.).
- **Tests** : Ajouter des tests unitaires et d'intégration complets.

## Architecture

### Séparation des responsabilités

**Phase 2 (Serveur MCP canonique)** :
- Tools bas niveau : CRUD foods/units
- Exposition via MCP
- Réutilisation par tous les clients

**Phase 3 (Workflow métier)** :
- Capacités composées : logique métier
- Utilisation des tools bas niveau
- Orchestration et workflows complexes

### Flux de données

```
Recette (ingrédients texte)
    ↓
validate_ingredients_structure (validation)
    ↓
intelligent_ingredient_structurer (structuration)
    ↓
complete_ingredient_migration (création foods/units via MCP)
    ↓
correct_existing_foods (corrections via MCP)
```

## Fichiers modifiés/créés

### Créés
- `mealie-workflow/skills/ingredient_optimizer_skill.py`
- `docs/specs/ingredient-optimization-phase3.md` (ce fichier)

### Modifiés
- `mealie-workflow/workflow_orchestrator.py`

## Références

- Phase 2 (Restauration tools bas niveau) : `docs/specs/ingredient-tools-restoration.md`
- Inventory complet : `docs/specs/ingredient-tools-inventory.md`
- Pattern skills existants : `mealie-workflow/skills/`
