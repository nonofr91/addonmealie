# Nutrition Addon MCP vs REST API

## Contexte

L'addon `mealie-nutrition-advisor` est un service Docker autonome qui effectue des opérations sur Mealie :
- Lecture des recettes pour calcul nutritionnel
- Patch du champ nutrition via API REST
- Création de mealplans pour le planning hebdomadaire

L'addon utilise actuellement l'API REST directe via `MealieClient` dans `mealie_sync.py`.

## Problème

Selon les règles de gouvernance du repo :
- Pour les opérations sur Mealie, préférer les MCP disponibles avant d'écrire une logique ad hoc
- Le serveur canonique `mealie-mcp-server/` est la source de vérité pour l'accès MCP à Mealie

L'addon nutrition utilise l'API REST directe, ce qui semble contradictoire avec cette règle.

## Analyse

### Options

#### Option 1 : Utiliser le MCP Mealie

**Avantages :**
- Respecte la règle de gouvernance "préférer les MCP disponibles"
- Réutilise la source de vérité canonique
- Abstraction uniforme pour les opérations Mealie

**Inconvénients :**
- Nécessite d'intégrer un client MCP dans l'addon
- Ajoute une dépendance à un service externe (serveur MCP Mealie)
- Complexifie le déploiement (deux services au lieu d'un)
- Le MCP Mealie est conçu pour être utilisé par des agents AI, pas par des services autonomes

#### Option 2 : Conserver l'API REST directe

**Avantages :**
- L'addon est autonome et ne dépend pas d'un service MCP externe
- Déploiement plus simple (un seul service)
- Architecture existante fonctionnelle
- L'API REST est une interface publique de Mealie (autorisée par les contraintes plateforme)

**Inconvénients :**
- Ne respecte pas strictement la règle "préférer les MCP disponibles"
- Duplication de logique d'accès Mealie (déjà dans mealie-mcp-server)

### Contraintes spécifiques à l'addon nutrition

L'addon nutrition est déployé comme service Docker autonome avec :
- Sa propre API FastAPI
- Sa propre UI Streamlit
- Ses propres calculs nutritionnels (cache OFF, LLM fallback)
- Son propre système de profils et planning

L'intégration avec le MCP Mealie nécessiterait :
1. Démarrer le serveur MCP Mealie comme service Docker
2. Configurer l'addon pour se connecter au MCP Mealie
3. Installer un client MCP (ex: `mcp-client` ou `anthropic-mcp`)
4. Remplacer tous les appels API REST par des appels MCP

## Décision

**Conserver l'API REST directe pour l'addon nutrition.**

### Rationale

1. **Architecture de service autonome** : L'addon nutrition est conçu comme un service Docker autonome avec sa propre API et UI. Intégrer le MCP Mealie ajouterait une dépendance externe inutile.

2. **Interface publique autorisée** : L'API REST de Mealie est une interface publique explicitement autorisée par `docs/decisions/mealie-platform-constraints.md`. Les addons peuvent utiliser l'API publique.

3. **Déploiement simplifié** : Conserver l'API REST permet un déploiement simple (un seul service) sans nécessiter le serveur MCP Mealie.

4. **Cas d'usage différent** : Le MCP Mealie est optimisé pour les agents AI qui interagissent de manière conversationnelle avec Mealie. L'addon nutrition est un service de calcul et planning automatisé.

5. **Règle de gouvernance contextualisée** : La règle "préférer les MCP disponibles" s'applique aux nouvelles intégrations. L'addon nutrition existe déjà avec une architecture REST fonctionnelle.

## Conséquences

- L'addon nutrition continue d'utiliser l'API REST directe via `MealieClient`
- Le commentaire dans `mealie_sync.py` documente ce choix architectural
- Pour les futurs addons, évaluer l'utilisation du MCP Mealie au cas par cas selon le contexte

## Exceptions

Si un futur addon nécessite des capacités avancées du MCP Mealie non disponibles via l'API REST (ex: recherche sémantique, filtrage complexe), alors l'intégration MCP sera envisagée.

