# Phase 4 : Évaluation - Import IA avancé

## Contexte

L’inventory mentionne des outils "Import IA avancé" qui étaient historiquement disponibles mais qui n’ont pas été repris dans le serveur MCP canonique. Cette phase évalue leur pertinence par rapport au workflow actuel.

## Outils à évaluer

1. **`scrape_recipe`** - Importe une recette depuis une URL (différent de create_recipe)
2. **`import_ia_bulk`** - Importe en masse des recettes françaises
3. **`get_import_ia_status`** - Affiche le statut du cookbook Import IA
4. **`organize_import_ia`** - Organise les recettes dans le cookbook Import IA

## Évaluation détaillée

### 1. scrape_recipe

**Statut** : ✅ **DÉJÀ COUVERT**

**Implémentation existante** :
- `mealie-workflow/skills/recipe_scraper_skill.py` 
- Méthode `scrape_specific_recipe(url)` disponible
- Intégré dans le workflow orchestrator

**Recommandation** : Non nécessaire à implémenter séparément. La capacité existe déjà dans le workflow canonique via le scraper skill.

### 2. import_ia_bulk

**Statut** : ✅ **DÉJÀ COUVERT**

**Implémentation existante** :
- `mealie-workflow/mcp3_import_batch.py`
- Fonction `import_batch(recipes_list, batch_size, delay)` disponible
- Chargé automatiquement dans `mcp_auth_wrapper.py`
- Gère l’import par lots avec délais configurables

**Recommandation** : Non nécessaire à implémenter séparément. La capacité existe déjà via le wrapper MCP.

### 3. get_import_ia_status

**Statut** : ⚠️ **WORKFLOW SPÉCIFIQUE**

**Description** : Affiche le statut du cookbook "Import IA"

**Analyse** :
- Ce n’est pas une fonctionnalité API Mealie générique
- C’est un pattern organisationnel spécifique : un cookbook nommé "Import IA" sert de zone tampon pour les recettes importées
- Le workflow actuel n’utilise pas ce pattern de cookbook tampon
- Les recettes sont importées directement dans les cookbooks cibles

**Recommandation** : **NON PRIORITAIRE** - Ce pattern organisationnel spécifique peut être remplacé par :
- Tags de tracking (ex: "Import IA", "À valider")
- Rapports d’import générés par le workflow
- Filtres par date d’import

### 4. organize_import_ia

**Statut** : ⚠️ **WORKFLOW SPÉCIFIQUE**

**Description** : Organise les recettes dans le cookbook Import IA

**Analyse** :
- Similaire à `get_import_ia_status`, c’est un pattern organisationnel spécifique
- Le workflow actuel organise directement lors de l’import (catégories, tags)
- Pas besoin d’une étape d’organisation post-import dans un cookbook tampon

**Recommandation** : **NON PRIORITAIRE** - L’organisation est intégrée dans le workflow actuel via :
- Catégorisation lors de la structuration
- Tagging automatique
- Mapping direct vers les cookbooks cibles

## Conclusions

### Capacités déjà couvertes
- ✅ Scraping de recettes depuis URLs
- ✅ Import par lots avec gestion des délais
- ✅ Workflow complet scraping → structuration → import

### Capacités non pertinentes
- ❌ Gestion spécifique du cookbook "Import IA"
- ❌ Organisation post-import dans un cookbook tampon

### Pattern "Import IA" historique

Le concept "Import IA" était un pattern organisationnel :
1. Importer les recettes dans un cookbook tampon "Import IA"
2. Valider et organiser dans ce cookbook
3. Déplacer vers les cookbooks finaux

Ce pattern a été **supplanté** par le workflow canonique :
- Validation avant import
- Organisation directe lors de la structuration
- Import direct dans les cookbooks cibles

## Recommandation finale

**Phase 4 ne nécessite PAS d’implémentation**.

Les capacités techniques de scraping et d’import batch sont déjà présentes dans le workflow canonique. Les outils spécifiques de gestion du cookbook "Import IA" sont basés sur un pattern organisationnel historique qui n’est plus pertinent avec le workflow actuel.

## Alternatives pour le tracking d’import

Si le besoin de tracking des imports persiste, utiliser :

### Tags de tracking
- Tag "Import IA" pour identifier les recettes importées automatiquement
- Tag "À valider" pour les recettes nécessitant une revue
- Tag "Validé" après revue manuelle

### Rapports d’import
- Le workflow génère déjà des rapports d’import
- Ces rapports peuvent être utilisés pour le tracking
- Stockés dans `mealie-workflow/import_reports/`

### Filtres par date
- Filtrer les recettes par date de création
- Identifier les imports récents
- Pas besoin de cookbook séparé

## Fichiers de référence

- Scraper skill : `mealie-workflow/skills/recipe_scraper_skill.py`
- Import batch : `mealie-workflow/mcp3_import_batch.py`
- Wrapper : `mealie-workflow/mcp_auth_wrapper.py`
- Inventory : `docs/specs/ingredient-tools-inventory.md`

## État de Phase 4

- ✅ Évaluation terminée
- ✅ Capacités existantes identifiées
- ✅ Pattern historique analysé
- ✅ Recommandation formulée : **AUCUNE IMPLÉMENTATION NÉCESSAIRE**
