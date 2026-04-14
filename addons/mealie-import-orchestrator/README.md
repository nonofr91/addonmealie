# Mealie Import Orchestrator

Addon externe d'orchestration pour piloter le workflow canonique d'import de recettes vers Mealie.

## Usage local recommandé

Cet addon est conçu pour être testé d'abord contre la stack locale `packages/mealie-dev-stack/`, puis validé dans Coolify.

Consulter aussi `docs/specs/local-addon-dev-flow.md` pour le parcours développeur local complet.

## Préparation

1. Lancer une instance locale Mealie avec `packages/mealie-dev-stack/`
2. Copier `.env.template` vers `.env`
3. Renseigner `MEALIE_BASE_URL` et `MEALIE_API_KEY`
4. Installer l'addon localement si besoin

## Variables d'environnement principales

- `MEALIE_BASE_URL` : URL de l'instance Mealie cible
- `MEALIE_API_KEY` : clé API Mealie
- `MEALIE_IMPORT_ORCHESTRATOR_REPO_ROOT` : racine du monorepo si nécessaire
- `MEALIE_IMPORT_ORCHESTRATOR_WORKFLOW_PATH` : chemin du workflow canonique si différent du défaut
- `MEALIE_IMPORT_ORCHESTRATOR_ENABLE_SCRAPING` : active explicitement le scraping si un backend réel est prêt

## Exemples

### Smoke test local recommandé

```bash
smoke-test
```

Ce scénario valide que la commande `status` de l'addon renvoie un JSON exploitable dans le contexte local du monorepo.

### Vérifier le statut

```bash
mealie-import-orchestrator status
```

### Lancer un import sur un fichier structuré existant

```bash
mealie-import-orchestrator step importing --structured-filename path/to/structured.json
```

### Lancer une structuration sur un fichier existant

```bash
mealie-import-orchestrator step structuring --scraped-filename path/to/scraped.json
```

### Premier scénario local utile

Une fixture canonique est disponible pour tester l'import local :

```bash
mealie-import-orchestrator step importing --structured-filename addons/mealie-import-orchestrator/tests/fixtures/structured_recipe.json
```

Ce scénario suppose qu'une instance Mealie locale est démarrée et qu'une clé API locale valide est configurée.

## Limites actuelles

Le scraping complet est désactivé par défaut dans le runtime addon.

Il ne doit être activé explicitement que si le backend de scraping réellement compatible avec l'environnement d'exécution est disponible.

## Validation cible

- test local contre `packages/mealie-dev-stack/`
- validation ensuite en runtime conteneurisé dans Coolify
