# Architecture - Mealie Addons Platform

## Vue d'ensemble

La plateforme Mealie Addons est conçue comme une suite de services Docker indépendants qui s'intègrent à Mealie via son API publique, sans jamais modifier l'image Mealie elle-même.

### Principes architecturaux

- **Séparation des responsabilités** : chaque addon a une fonctionnalité unique et bien définie
- **Communication via API** : tous les échanges passent par l'API REST de Mealie ou MCP
- **Déploiement conteneurisé** : chaque addon est un service Docker autonome
- **Configuration externalisée** : secrets et settings via variables d'environnement
- **Observabilité** : logs stdout/stderr, healthchecks, métriques

## Diagramme système

```
┌─────────────────────────────────────────────────────────────┐
│                        Docker Host                           │
│                                                             │
│  ┌─────────────────┐         ┌──────────────────────────┐  │
│  │   Mealie Core   │         │   Coolify / Orchestrateur │  │
│  │  (Docker image)  │◄────────┤      (gestion conteneurs)   │  │
│  └────────┬────────┘         └──────────────────────────┘  │
│           │ API REST                                             │
│    ┌──────┴──────┬──────────┬──────────┬──────────┐          │
│    │             │          │          │          │          │
│ ┌──▼────────┐ ┌──▼───────┐ ┌▼─────────┐ ┌▼────────┐      │
│ │  Import   │ │ Nutrition│ │   MCP    │ │  Future │      │
│ │  Addon    │ │  Addon   │ │  Server  │ │  Addon  │      │
│ │(port 8000)│ │(port 8001)│ │(port MCP)│ │  ...    │      │
│ └──┬────────┘ └──┬───────┘ └┬─────────┘ └────────┘      │
│    │            │          │                             │
│    └────────────┴──────────┴─────────────────────────────┘  │
│                    Réseau Docker interne                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Clients externes                          │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Navigateur   │  │ Claude       │  │ Scripts      │      │
│  │ (Streamlit)  │  │ Desktop      │  │ personnalisés│      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                    HTTP / MCP                               │
└─────────────────────────────────────────────────────────────┘
```

## Composants

### Mealie Core

L'instance Mealie principale, déployée via le template officiel Docker.

- **Rôle** : Gestion des recettes, ingrédients, plans de repas, listes de courses
- **Interface** : API REST publique
- **Données** : Base de données interne (non modifiée par les addons)
- **Déploiement** : Conteneur Docker géré par Coolify ou Docker Compose

### Addons

#### mealie-import-orchestrator

**Responsabilité** : Import de recettes depuis le web et audit de qualité

- **Ports** : API 8000, UI 8501
- **Technologies** : FastAPI, Streamlit, BeautifulSoup, OpenAI (optionnel)
- **Communication** : API REST Mealie (lecture/écriture)
- **Stockage** : Cache local temporaire, images téléchargées

**Flux de données** :
```
URL recette → Scraping → Structuration → Validation → Mealie API
              ↓
         TheMealDB (images de fallback)
```

#### mealie-nutrition-advisor

**Responsabilité** : Calcul nutritionnel et planification de menus

- **Ports** : API 8001, UI 8502
- **Technologies** : FastAPI, Streamlit, Open Food Facts, LLM
- **Communication** : API REST Mealie (lecture/écriture)
- **Stockage** : Cache nutritionnel, profils du foyer

**Flux de données** :
```
Recette Mealie → Parsing ingrédients → Open Food Facts → Nutrition
                                              ↓
                                         LLM fallback
                                              ↓
                                    Enrichissement Mealie
```

#### mealie-mcp-server

**Responsabilité** : Pont MCP vers l'API Mealie pour assistants IA

- **Port** : Port MCP configurable
- **Technologies** : FastMCP, Pydantic
- **Communication** : MCP (Model Context Protocol)
- **Stockage** : Aucun (stateless)

**Outils MCP** (45 au total) :
- Recettes : CRUD, duplication, images, assets
- Listes de courses : CRUD, bulk, intégration recettes
- Organisation : catégories, tags
- Planning : repas, création bulk

### mealie-workflow

**Responsabilité** : Scripts et outils pour l'import et la qualité

- **Technologies** : Python, MCP Mealie
- **Usage** : Scripts CLI, workflows batch
- **Communication** : MCP Mealie

**Scripts principaux** :
- `multi_source_scraper.py` : Scraping multi-sources
- `quality_checker.py` : Audit de qualité des recettes
- `mcp3_import_batch.py` : Import batch via MCP
- `mealie_recipe_manager.py` : Gestion des recettes

## Communication entre composants

### API REST

Tous les addons communiquent avec Mealie via son API REST publique :

- **Authentification** : Token API via variable d'environnement
- **Base URL** : Configurable (local ou distant)
- **Endpoints** : Documentation officielle Mealie
- **Rate limiting** : Géré par Mealie

### MCP (Model Context Protocol)

Le serveur MCP permet aux assistants IA (Claude Desktop, etc.) d'interagir avec Mealie :

- **Protocole** : MCP standard
- **Transport** : stdio ou HTTP
- **Outils** : 45 outils API Mealie exposés
- **Configuration** : `claude_desktop_config.json`

### Communication inter-addons

Les addons peuvent communiquer entre eux via :

- **API REST** : Chaque addon expose son API
- **Réseau Docker** : Communication interne via nom de service
- **Exemple** : Import Addon → Nutrition Addon pour enrichissement automatique

## Découpage des responsabilités

### Import Addon
- ✅ Scraping de recettes
- ✅ Structuration des données
- ✅ Audit de qualité
- ❌ Calcul nutritionnel (délégué à Nutrition Addon)
- ❌ Planification de menus (délégué à Nutrition Addon)

### Nutrition Addon
- ✅ Calcul nutritionnel
- ✅ Gestion des profils
- ✅ Planification de menus
- ❌ Import de recettes (délégué à Import Addon)
- ❌ Scraping web (hors périmètre)

### MCP Server
- ✅ Exposition API Mealie via MCP
- ✅ Normalisation des réponses
- ❌ Logique métier (stateless)
- ❌ Calcul nutritionnel (lecture seule)

## Décisions d'architecture

Voir `docs/decisions/` pour les décisions détaillées :

- **addon-deployment-model.md** : Modèle de déploiement Docker séparé
- **ai-provider-abstraction.md** : Abstraction des providers IA
- **mealie-platform-constraints.md** : Contraintes de la plateforme Mealie
- **mcp-canonical-source.md** : MCP comme source canonique pour l'intégration IA

## Sécurité

### Secrets

- **Jamais versionnés** : Aucun token ou clé API dans le repo
- **Variables d'environnement** : Configuration externalisée
- **.env.template** : Exemples de configuration sans secrets

### Communication

- **HTTPS** : Recommandé pour les déploiements en production
- **Réseau Docker interne** : Communication entre services locaux
- **Authentification** : Tokens API Mealie, secrets addons

### Isolation

- **Conteneurs séparés** : Chaque addon dans son propre conteneur
- **Pas d'accès direct** : Aucun accès shell ou base de données Mealie
- **API publique uniquement** : Respect des contraintes Mealie

## Scalabilité

### Horizontal scaling

- **Addons stateless** : Peuvent être scalés horizontalement
- **Load balancing** : Via Coolify ou Docker Swarm
- **Cache distribué** : Pour le cache nutritionnel (future)

### Performance

- **Cache local** : TTL configurable pour les appels API externes
- **Batch operations** : Traitement par lots pour les imports
- **Async processing** : Pour les opérations longues (future)

## Observabilité

### Logging

- **Stdout/stderr** : Tous les logs vers stdout
- **Structured logging** : Format JSON (future)
- **Log levels** : Configurable via LOG_LEVEL

### Health checks

- **Endpoint /health** : Disponibilité du service
- **Endpoint /status** : État détaillé (connectivité Mealie, IA, etc.)
- **Docker healthcheck** : Intégré au Dockerfile

### Métriques

- **Prometheus** : Export de métriques (future)
- **Custom metrics** : Appels API, temps de réponse, erreurs

## Développement

### Structure de code

```
addons/mealie-xxx-orchestrator/
├── src/mealie_xxx_orchestrator/
│   ├── api.py          # FastAPI endpoints
│   ├── ui.py           # Streamlit interface
│   ├── cli.py          # CLI commands
│   ├── orchestrator.py # Core logic
│   └── config.py       # Configuration
├── Dockerfile          # Build image
├── docker-compose.yml  # Local dev
└── .env.template       # Config template
```

### Testing

- **Unit tests** : Tests de logique métier
- **Integration tests** : Tests avec Mealie mock
- **E2E tests** : Tests avec instance Mealie réelle (CI)

### CI/CD

- **GitHub Actions** : CI pour tests et linting
- **Docker publish** : Build et push automatique sur tag
- **Multi-registry** : GHCR principal, autres registres (future)

## Évolution

### Nouveaux addons

Pour créer un nouvel addon :

1. Créer un dossier dans `addons/`
2. Suivre la structure standard (api, ui, cli, orchestrator)
3. Utiliser les packages partagés dans `packages/`
4. Ajouter un Dockerfile et docker-compose.yml
5. Documenter dans README dédié
6. Ajouter au workflow Docker publish

### Packages partagés

Code réutilisable à extraire vers `packages/` :

- `mealie-dev-stack` : Outils de développement
- `mealie-api-client` : Client API Mealie (future)
- `mealie-nutrition-core` : Logique nutritionnelle (future)

### Intégrations futures

- **Kubernetes** : Helm charts pour déploiement K8s
- **Cloud providers** : AWS ECS, GCP Cloud Run
- **Monitoring** : Grafana, Prometheus
- **Tracing** : OpenTelemetry
