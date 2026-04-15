# Problème critique : Instance locale Mealie 3.14 ne préserve pas les données

## Date
2026-04-12

## Problème identifié

L'instance locale Mealie v3.14.0 ne préserve pas les données envoyées dans le payload lors de la création de recettes via l'API, même avec le format correct selon la documentation OpenAPI 3.14.

## Symptômes

Les données envoyées dans le payload sont correctes :
- recipeServings: 2.0
- recipeYield: "2 servings"
- prepTime: "PT10M"
- cookTime: "PT20M"
- totalTime: "PT30M"
- recipeIngredient: 2 ingrédients
- recipeInstructions: 2 instructions

Mais les données stockées dans Mealie sont incomplètes :
- recipeServings: 0.0
- recipeYield: None
- prepTime: None
- cookTime: None
- totalTime: None
- recipeIngredient: 1 ingrédient
- recipeInstructions: 1 instruction

## Tests effectués

1. **Test avec format simple (chaînes)** : Même problème
2. **Test avec format structuré (objets)** : Même problème
3. **Test direct via API (sans MCP)** : Même problème
4. **Vérification des logs Docker** : Pas d'erreurs, les requêtes renvoient 201 Created

## Investigation des logs

Les logs du conteneur Docker mealie-local-dev montrent :
- Les requêtes POST /api/recipes renvoient 201 Created
- Aucune erreur visible dans les logs
- L'API accepte bien les requêtes mais ne préserve pas les données

## Investigation du schéma SQLite

Examen de la base de données SQLite locale (`/app/data/mealie.db`) :

### Table `recipes`
Les champs de la table `recipes` sont :
- `recipe_servings`: FLOAT avec valeur par défaut '0'
- `recipe_yield_quantity`: FLOAT avec valeur par défaut '0'
- `prep_time`, `cook_time`, `total_time`: VARCHAR

### Table `recipes_ingredients`
Les champs de la table `recipes_ingredients` sont :
- `quantity`: INTEGER (au lieu de FLOAT)

### Données stockées
Les données réelles stockées dans la base de données montrent :
- `recipe_servings`: 0.0 (au lieu de 2.0 envoyé)
- `recipe_yield_quantity`: 0.0 (au lieu de 2.0 envoyé)
- `prep_time`, `cook_time`, `total_time`: NULL (au lieu de "PT10M", "PT20M", "PT30M" envoyés)
- `quantity` dans `recipes_ingredients`: 0 (au lieu de 2.0 envoyé)

## Cause racine identifiée

Le schéma de la base de données SQLite locale est incohérent avec l'API 3.14 :
1. Les champs `recipe_servings` et `recipe_yield_quantity` sont FLOAT avec une valeur par défaut de 0
2. Le champ `quantity` dans `recipes_ingredients` est INTEGER au lieu de FLOAT
3. Les champs de temps sont VARCHAR mais ne sont pas correctement remplis

Cela explique pourquoi les données envoyées dans le payload ne sont pas correctement stockées dans la base de données locale. L'instance locale Mealie 3.14 a un schéma de base de données incompatible avec l'API 3.14.

## Origine de l'incohérence

**Important : Cette incohérence n'a pas été créée manuellement.** Elle provient des migrations automatiques du conteneur Docker lors de l'initialisation.

**Détails du déploiement Docker :**
- Image : `ghcr.io/mealie-recipes/mealie:latest`
- Logs de démarrage montrent des migrations automatiques :
  - "Migration needed. Performing migration..."
  - "Running upgrade 1fe4bd37ccc8 -> 602927e1013e, 'add the rest of the schema.org nutrition properties'"
  - "Running new model migration (migrate_recipe_last_made_to_household)"
  - "Running new model migration (migrate_foods_on_hand_to_household)"
  - "Running new model migration (migrate_tools_on_hand_to_household)"
  - "Running upgrade 7cf3054cbbcc -> d7b3ce6fa31a, empty migration to fix food flag data"

Le schéma de base de données a été créé automatiquement par ces migrations, et il est incompatible avec l'API 3.14. C'est un problème de configuration du déploiement Docker local, pas une modification manuelle.

## Recherche de problèmes similaires signalés

**Issue GitHub #4881 : "[BUG] - Yield migration sets 'Servings' to '0' in some cases"**

Cette issue décrit un problème similaire mais différent :
- **Problème signalé** : Les migrations de yield/servings mettent certaines recettes à Servings = 0 lors de la conversion de données non structurées en données structurées
- **Version affectée** : v2.4.2 (ancienne version)
- **Statut** : Fermée comme "completed" - les développeurs considèrent que ce n'est pas un bug mais une conséquence inévitable de la conversion de données
- **Différence avec notre problème** : Notre problème concerne le stockage de NOUVELLES données via l'API, pas la migration de données existantes

**Notre problème spécifique :**
- Nous envoyons des données via l'API avec des valeurs correctes (recipeServings: 2.0, recipeYield: "2 servings")
- Ces données ne sont pas stockées correctement dans la base de données locale
- Ce n'est pas un problème de migration de données existantes, mais un problème de stockage de nouvelles données via l'API
- Le schéma de base de données local est incompatible avec l'API 3.14

**Conclusion :**
Notre problème est différent de l'issue #4881 et n'a pas été signalé spécifiquement. L'incohérence du schéma de base de données local avec l'API 3.14 semble être un problème spécifique à notre déploiement Docker local.

## Recommandations pour résoudre le problème de l'instance locale

### Option 1 : Mettre à jour l'image Docker locale
- Utiliser une version spécifique de l'image Docker (au lieu de `latest`) qui a un schéma de base de données compatible avec l'API 3.14
- Vérifier les notes de version de Mealie pour identifier les versions stables
- Recréer le conteneur avec la nouvelle image et une base de données fraîche

### Option 2 : Recréer la base de données locale
- Supprimer le volume Docker actuel contenant la base de données
- Recréer le conteneur pour forcer une nouvelle initialisation de la base de données
- Vérifier si les migrations créent un schéma compatible avec l'API 3.14

### Option 3 : Accepter les limitations et utiliser Coolify
- Accepter que l'instance locale a des limitations de schéma
- Utiliser l'instance Coolify pour les tests d'intégration malgré les versions différentes
- Documenter les correctifs comme valides pour l'API 3.14 mais non testables sur l'instance locale

### Option 4 : Signaler le problème aux développeurs Mealie
- Créer une issue GitHub pour signaler l'incohérence du schéma de base de données local avec l'API 3.14
- Fournir les détails du schéma SQLite observé et les tests effectués
- Demander si c'est un bug connu ou une limitation attendue

## Recommandation actuelle

**Option 3** est la plus pragmatique pour continuer le développement :
- Les correctifs de mapping sont valides et correspondent au schéma API 3.14
- L'instance Coolify peut être utilisée pour validation en production
- Le problème de l'instance locale est documenté pour investigation future
- Cela évite de perdre du temps à déboguer un problème spécifique au déploiement local

## Résultat du test avec base de données fraîche

**Test effectué :**
- Arrêt du conteneur Docker mealie-local-dev
- Suppression du volume Docker contenant la base de données
- Recréation du conteneur avec l'image Docker `ghcr.io/mealie-recipes/mealie:latest`
- Création d'un nouvel utilisateur et obtention d'une nouvelle clé API
- Test d'import avec la nouvelle clé API

**Résultat :**
Le problème persiste même avec une base de données fraîche :
- recipeServings: 0.0 (au lieu de 2.0)
- recipeYieldQuantity: 0.0 (au lieu de 2.0)
- recipeYield: null (au lieu de "2 servings")
- totalTime: null (au lieu de "PT30M")
- prepTime: null (au lieu de "PT10M")
- cookTime: null (au lieu de "PT20M")
- recipeIngredient: quantity: 0.0 (au lieu de 2.0)

**Conclusion :**
Le problème n'est pas spécifique à l'ancienne base de données, mais inhérent à cette version de Mealie (l'image Docker `ghcr.io/mealie-recipes/mealie:latest`). Le schéma de base de données est incompatible avec l'API 3.14, même avec une base de données fraîche. Cela confirme que l'option 2 (recréer la base de données) ne résout pas le problème.

## Nouvelle découverte : Mécanisme de migration intégré

**Observation utilisateur :**
Au démarrage de Mealie, l'interface a proposé une option de migration des recettes. Cela suggère qu'il existe un mécanisme de migration intégré dans Mealie pour convertir les structures de base de données.

**Documentation trouvée :**
- Le FAQ Mealie mentionne : "This process was required in previous versions of Mealie, however we've automated the database migration process to make it easier to upgrade."
- Mealie utilise Alembic pour les migrations de base de données
- Les migrations automatiques sont exécutées lors des mises à jour

**Hypothèse :**
Il est possible que le mécanisme de migration intégré puisse être utilisé pour convertir le schéma de base de données incompatible en un schéma compatible avec l'API 3.14.

**Investigation en cours :**
- Déterminer comment activer ou forcer la migration de base de données
- Vérifier si la migration peut corriger l'incohérence du schéma
- Tester si la migration résout le problème de perte de données

**Résultat de l'investigation de l'interface de migration :**
L'option de migration disponible dans l'interface Mealie locale (http://127.0.0.1:9925/group/migrations) est pour importer des recettes depuis une version antérieure à 1.0 de Mealie. Cette option ne résout pas notre problème de schéma de base de données incompatible avec l'API 3.14.

**Conclusion finale sur le mécanisme de migration :**
Le mécanisme de migration intégré de Mealie est conçu pour :
- Migrer des données depuis des versions pré-v1.0
- Exécuter des migrations automatiques lors des mises à jour
- Corriger des problèmes de données spécifiques

Il n'y a pas d'option de migration disponible pour corriger l'incohérence du schéma de base de données avec l'API 3.14.

## Analyse des releases GitHub de Mealie

**Versions récentes identifiées :**
- v3.14.0 (latest) - Version actuelle déployée localement
- v3.13.1
- v3.13.0
- v3.12.0
- v3.9.2
- v3.9.1

**Changements notables dans v3.14.0 :**
- Améliorations du parser NLP pour les recettes non-anglaises
- Correction de bugs d'import HTML/JSON (#7330)
- Correction de la préservation des slugs de recette lors de l'hydratation (#7294)
- Mise à jour de la dépendance ingredient-parser-nlp à v2.6.0

**Changements notables dans v3.13.0 :**
- Nouvelle fonctionnalité : standardisation des unités pour permettre les conversions
- Import de recettes depuis YouTube, TikTok, Instagram
- Amélioration du scraper
- Mise à jour de la dépendance openai à v2.28.0

**Changements notables dans v3.12.0 :**
- Optimisation majeure du script de healthcheck
- Amélioration du parser NLP
- Correction de bugs liés aux ingrédients

**Hypothèse :**
Le problème de schéma incompatible pourrait être lié aux changements dans v3.13.0 ou v3.14.0, notamment :
- La standardisation des unités introduite dans v3.13.0
- Les changements dans le parser NLP dans v3.14.0
- Les corrections d'import dans v3.14.0

**Recommandation :**
Tester une version antérieure (v3.12.0 ou v3.9.x) pour voir si le schéma de base de données est compatible avec l'API de cette version. Cela permettrait de déterminer si le problème est spécifique à v3.13.x ou v3.14.0.

## Découverte cruciale : Coolify utilise aussi v3.14.0 et fonctionne correctement

**Informations fournies par l'utilisateur :**
- Version Coolify : v3.14.0
- Build : 085ecbaae38e3243ec251528ce77534f8a671db8
- Mode de l'application : Production
- Type de base de données : sqlite
- URL de la base de données : sqlite:////app/data/mealie.db
- Version du Scraper de recette : 15.11.0

**Conclusion :**
La même version v3.14.0 fonctionne correctement sur Coolify mais pas localement. Cela contredit notre hypothèse que le problème est inhérent à la version v3.14.0 de Mealie.

**Nouvelle hypothèse :**
Le problème est spécifique à la configuration locale, pas à la version de Mealie elle-même. Les différences possibles entre Coolify et local :
- Configuration Docker différente
- Variables d'environnement différentes
- Build différent (085ecbaae38e3243ec251528ce77534f8a671db8 vs latest)
- Initialisation de la base de données différente

**Action requise :**
Comparer la configuration Coolify et locale pour identifier la différence spécifique qui cause le problème de schéma incompatible.

## Nouvelle direction : Le problème est dans le MCP, pas dans l'instance Mealie

**Découverte cruciale :**
L'utilisateur a confirmé que le MCP fonctionne sur Coolify avec la même version v3.14.0. Cela signifie que le problème n'est pas dans l'instance Mealie locale, mais dans le MCP lui-même.

**Conclusion :**
- L'instance Mealie locale v3.14.0 fonctionne correctement (même version que Coolify)
- Le MCP fonctionne sur Coolify mais pas localement
- Le problème est donc dans le MCP local (`mealie-workflow/mcp_auth_wrapper.py`)

**Hypothèse :**
Le MCP local utilise une implémentation différente de celle utilisée sur Coolify. Coolify utilise probablement le MCP officiel `mealie-test` tandis que le local utilise un wrapper personnalisé dans `mealie-workflow/mcp_auth_wrapper.py`.

**Action requise :**
Investiguer le MCP local pour comprendre pourquoi il ne fonctionne pas correctement avec l'instance Mealie locale v3.14.0. Comparer l'implémentation locale avec le MCP officiel utilisé sur Coolify.

## Test avec le MCP officiel : Même problème sur l'instance locale

**Test effectué :**
J'ai testé le MCP officiel (`mcp3_create_recipe`) avec l'instance locale et le résultat montre le même problème de données incomplètes :
- `recipeServings: 0.0`
- `recipeYieldQuantity: 0.0`
- `recipeYield: null`
- `totalTime: null`
- `prepTime: null`
- `cookTime: null`
- `recipeIngredient: quantity: 0.0`

**Conclusion :**
Le problème n'est PAS dans le MCP local (`mealie-workflow/mcp_auth_wrapper.py`), mais bien dans l'instance Mealie locale elle-même. Le MCP officiel a le même problème que le MCP local.

**Nouvelle hypothèse :**
Il y a une différence entre l'instance locale et l'instance Coolify qui n'est pas liée à la version de Mealie (toutes les deux sont v3.14.0), mais peut-être à :
- La configuration de l'instance
- L'initialisation de la base de données
- Les variables d'environnement
- Le build spécifique de l'image Docker

**Action requise :**
Identifier la différence spécifique entre l'instance locale et l'instance Coolify qui cause ce problème de perte de données.

## Test avec les variables d'environnement de Coolify : Problème persiste

**Test effectué :**
J'ai ajouté les variables d'environnement de Coolify à la configuration locale :
- `ALLOW_SIGNUP=true`
- `PUID=1000`
- `PGID=1000`
- `TZ=Europe/Paris`
- `MAX_WORKERS=10`
- `WEB_CONCURRENCY=1`

J'ai recréé le conteneur avec ces nouvelles variables d'environnement et testé l'import avec le MCP officiel.

**Résultat :**
Le problème persiste même avec les mêmes variables d'environnement que Coolify :
- `recipeServings: 0.0`
- `recipeYieldQuantity: 0.0`
- `recipeYield: null`
- `totalTime: null`
- `prepTime: null`
- `cookTime: null`
- `recipeIngredient: quantity: 0.0`

**Conclusion :**
Les variables d'environnement ne sont pas la cause du problème. La différence entre l'instance locale et l'instance Coolify doit être ailleurs :
- La configuration de l'instance (BASE_URL, SERVICE_URL_MEALIE_9000)
- Le build spécifique de l'image Docker
- L'initialisation de la base de données
- Une autre différence de configuration

**Action requise :**
Investiguer d'autres différences possibles entre l'instance locale et l'instance Coolify, notamment la configuration BASE_URL et SERVICE_URL_MEALIE_9000.

## Test avec les variables BASE_URL et SERVICE_URL_MEALIE_9000 : Problème persiste

**Test effectué :**
J'ai ajouté les variables d'environnement BASE_URL et SERVICE_URL_MEALIE_9000 à la configuration locale :
- `BASE_URL=http://127.0.0.1:9925`
- `SERVICE_URL_MEALIE_9000=http://127.0.0.1:9925`

J'ai recréé le conteneur avec ces nouvelles variables d'environnement et testé l'import avec le MCP officiel.

**Résultat :**
Le problème persiste même avec les variables BASE_URL et SERVICE_URL_MEALIE_9000 :
- `recipeServings: 0.0`
- `recipeYieldQuantity: 0.0`
- `recipeYield: null`
- `totalTime: null`
- `prepTime: null`
- `cookTime: null`
- `recipeIngredient: quantity: 0.0`

**Conclusion :**
Les variables BASE_URL et SERVICE_URL_MEALIE_9000 ne sont pas la cause du problème.

## Conclusion finale de l'investigation

Après de nombreux tests et investigations, nous avons établi les faits suivants :

1. **L'instance Mealie locale v3.14.0 a un problème inhérent de perte de données** lors de l'import via l'API
2. **L'instance Coolify v3.14.0 fonctionne correctement** avec la même version
3. **Le problème n'est pas dans le MCP** (ni local ni officiel)
4. **Le problème n'est pas dans les variables d'environnement** (ni ALLOW_SIGNUP, PUID, PGID, TZ, MAX_WORKERS, WEB_CONCURRENCY, ni BASE_URL, SERVICE_URL_MEALIE_9000)
5. **Le problème n'est pas dans le schéma de base de données** (même après recréation complète)
6. **Le problème n'est pas dans la version de Mealie** (v3.14.0 fonctionne sur Coolify)

**Hypothèse finale :**
La différence entre l'instance locale et l'instance Coolify pourrait être :
- Le build spécifique de l'image Docker (085ecbaae38e3243ec251528ce77534f8a671db8 vs latest)
- Une différence de configuration que nous n'avons pas identifiée
- Un problème spécifique à l'environnement local (Docker, OS, etc.)

**Recommandation :**
Utiliser l'instance Coolify pour les tests d'intégration et le développement, car l'instance locale a un problème non résolu qui empêche la validation correcte des imports. L'instance locale peut être utilisée pour d'autres tests mais ne devrait pas être utilisée pour valider l'import de recettes.

## Test curl direct : L'API locale renvoie des données incorrectes

**Test effectué :**
J'ai testé l'API locale directement avec curl :
1. POST `/api/recipes` pour créer une recette avec des données spécifiques
2. GET `/api/recipes/test-curl` pour récupérer la recette créée

**Payload envoyé :**
```json
{
  "name": "Test curl",
  "description": "Test direct API",
  "recipeIngredient": [{"note": "2 gousses d'ail", "quantity": 2}],
  "recipeInstructions": [{"text": "Écraser l'ail"}],
  "recipeServings": 4,
  "prepTime": "PT15M",
  "cookTime": "PT20M",
  "totalTime": "PT35M"
}
```

**Résultat :**
La recette créée contient des données complètement différentes de celles envoyées :
- `note: "1 Cup Flour"` au lieu de `"2 gousses d'ail"`
- `text: "Recipe steps as well as other fields in the recipe page support markdown syntax..."` au lieu de `"Écraser l'ail"`
- `recipeServings: 0.0` (au lieu de 4)
- `recipeYieldQuantity: 0.0`
- `totalTime: null` (au lieu de PT35M)
- `prepTime: null` (au lieu de PT15M)
- `cookTime: null` (au lieu de PT20M)
- `recipeIngredient: quantity: 0.0` (au lieu de 2)

**Conclusion :**
L'API locale renvoie une recette par défaut ou une recette de démo au lieu de celle que nous avons envoyée. Cela confirme qu'il y a un problème majeur avec l'API locale qui ne peut pas être résolu par la configuration ou les variables d'environnement.

## Problème identifié : Les MCP Cascade officiels ont un problème de format des données

**Test effectué :**
J'ai testé les MCP Cascade officiels (`mcp3_create_recipe`) avec Coolify et le résultat montre le même problème de données incomplètes :
- `recipeServings: 0.0`
- `recipeYieldQuantity: 0.0`
- `totalTime: null`
- `prepTime: null`
- `cookTime: null`
- `recipeIngredient: quantity: 0.0`

**Cause du problème :**
Les MCP Cascade officiels envoient les ingrédients comme des chaînes JSON dans le champ `note` au lieu d'objets structurés :
```json
{
  "note": "{\"note\": \"2 gousses d'ail\", \"quantity\": 2, \"unit_id\": null, \"food_id\": null}",
  "display": "{\"note\": \"2 gousses d'ail\", \"quantity\": 2, \"unit_id\": null, \"food_id\": null}"
}
```

**Conclusion :**
Le problème n'est pas spécifique à l'instance locale Mealie, mais dans la façon dont les MCP Cascade officiels envoient les données. Les MCP Cascade officiels ne fonctionnent pas correctement avec Mealie.

**Solution :**
Utiliser le wrapper MCP local (`mcp_auth_wrapper.py`) pour le chemin canonique d'orchestration, au lieu des MCP Cascade officiels. La restauration de ce chemin a confirmé que le workflow et le payload sont corrects, mais n'a pas supprimé le problème de persistance de l'instance locale.

## Confirmation finale après restauration du workflow canonique

**Test confirmé :**
Le scénario canonique de l'addon a été relancé avec succès :
`python3 -m mealie_import_orchestrator step importing --structured-filename tests/fixtures/structured_recipe.json`

Le workflow canonique est de nouveau opérationnel :
- le wrapper MCP local est bien utilisé
- l'import de la fixture se termine avec succès
- un rapport d'import est généré
- la recette est créée puis relue via le wrapper local

**Payload confirmé avant l'appel API :**
- `recipeServings: 2.0`
- `recipeYield: 2 servings`
- `prepTime: PT10M`
- `cookTime: PT20M`
- `totalTime: PT30M`
- `recipeIngredient: 2 ingrédients`
- `recipeInstructions: 2 instructions`

**Lecture post-import confirmée :**
Malgré un import exécuté avec succès, la recette relue dans Mealie contient encore des valeurs incorrectes :
- `recipeServings: 0.0`
- `recipeYieldQuantity: 0.0`
- `recipeYield: null`
- `prepTime: null`
- `cookTime: null`
- `totalTime: null`
- premier ingrédient remplacé par `1 Cup Flour`
- première instruction remplacée par le texte markdown de démonstration

**Conclusion confirmée :**
Le workflow canonique et le payload applicatif sont corrects. La corruption ou substitution des données se produit côté instance Mealie locale au moment de la persistance ou de la restitution des recettes.

## Impact

- Impossible de valider le workflow d'import avec IA sur l'instance locale
- Les recettes importées ont des données incomplètes
- Les tests d'intégration ne sont pas fiables

## Hypothèses

1. **Bug dans l'instance locale** : L'instance locale pourrait avoir un bug qui n'existe pas en production
2. **Configuration de l'instance locale** : L'instance locale pourrait avoir une configuration différente de la production
3. **Problème de base de données** : La base de données locale pourrait avoir un problème de schéma

## Recommandations

1. **Accepter les limitations de l'instance locale** : L'instance locale n'est pas fiable pour les tests d'intégration
2. **Utiliser l'instance Coolify pour les tests d'intégration** : Malgré les versions différentes, c'est la seule instance fiable
3. **Documenter les correctifs apportés** : Les correctifs de mapping sont valides et seront testés en production
4. **Mettre à jour l'instance locale dans le futur** : Quand une version plus stable sera disponible

## État

- **Investigation terminée** : Problème identifié mais non résolu (limitation de l'instance locale)
- **Non bloquant** : Les correctifs sont valides et seront testés en production
- **Priorité moyenne** : Impacte le développement local mais pas la production

## Actions futures

1. Tester le workflow complet sur l'instance Coolify malgré les versions différentes
2. Documenter le workflow IA validé pour la production
3. Mettre à jour l'instance locale quand une version plus stable sera disponible
4. Documenter les limitations de l'instance locale pour les futurs développements

---

## Résolution — 2026-04-15

### Migration vers Mealie v3.15.1

L'instance locale a été migrée vers `ghcr.io/mealie-recipes/mealie:v3.15.1`. Le problème de perte de données persiste sur `POST /api/recipes` avec un payload complet, car **l'API v3.x ne supporte que `{"name": "..."}` en POST**.

### Cause racine réelle

L'API `POST /api/recipes` de Mealie v3.x :
- Accepte uniquement le nom de la recette
- Retourne un slug (string) sans stocker les autres données
- Requiert un second appel `PATCH /api/recipes/{slug}` pour peupler le reste

Ce n'est pas un bug mais un **comportement intentionnel de l'API**.

### Solution implémentée : Two-step POST + PATCH

Dans `mealie-workflow/mcp_auth_wrapper.py`, `mcp3_create_recipe` suit désormais :

1. `POST /api/recipes` → `{"name": "..."}` → retourne le slug
2. `GET /api/recipes/{slug}` → récupère le vrai nom assigné (peut avoir suffixe -2, -3...)
3. `PATCH /api/recipes/{slug}` → payload complet (ingrédients, instructions, catégories, temps...)
4. `POST /api/recipes/{slug}/image` → scraping image depuis URL

### Résolution foods/units

Les foods et units dans les ingrédients sont résolus via un cache Mealie :
- `_build_mealie_cache` : charge tous les foods/units en une requête
- `_get_or_create_food` : lookup cache → réutilise ou crée
- `_get_or_create_unit` : idem pour les unités
- `_clean_food_name` : nettoie les prépositions françaises (`de `, `d'`, `des `...)

**Résultat** : recettes importées avec ingrédients structurés `{quantity, unit:{id,name}, food:{id,name}}`, catégories, tags, et image.

**Fichier de décision associé** : `docs/decisions/mealie-api-two-step-create.md`
