# Starter Pack Bootstrap Spec

## But

Décrire comment réutiliser ce dépôt comme template de projet sans copier aveuglément son historique métier.

## Périmètre

Cette spec couvre la réutilisation de la couche de gouvernance Windsurf et de la structure canonique du repo.

Elle ne couvre pas la migration automatique des scripts métier existants ni le nettoyage complet de l'historique du projet source.

## Noyau à réutiliser

### Gouvernance

- `AGENTS.md` - Règles de conduite pour les agents Cascade
- `CONTRIBUTING.md` - Workflow de développement et contribution
- `README.md` - Présentation du projet (à adapter)
- `LICENSE` - Licence (à adapter si nécessaire)
- `.gitignore` - Fichiers à ignorer (déjà configuré pour Python, Node.js, etc.)
- `.windsurf/rules/` - Règles de gouvernance par type de fichier/domaine
- `.windsurf/workflows/` - Workflows de cadrage, diagnostic, nettoyage et hygiène
- `.windsurf/skills/` - Expertises transverses (skills génériques)
- `docs/specs/` - Spécifications et décisions d'architecture
- `docs/decisions/` - Décisions d'architecture et arbitrages
- `docs/ROADMAP.md` - Feuille de route du projet (à adapter)
- `.github/workflows/` - Workflows GitHub Actions (CI, CodeQL, etc.)

### Structure canonique

- `addons/` - Addons externes (MCP, workers, pipelines)
- `packages/` - Packages partagés
- `scripts/` - Scripts d'orchestration et outils ponctuels
- `tests/` - Tests unitaires et intégration
- `docs/` - Documentation (specs, decisions, ROADMAP)
- `labs/` - Expérimentations temporaires (README.md avec règles)
- `tmp/` - Fichiers temporaires (à ignorer par git)
- `reports/` - Rapports générés (qualité, validation, etc.)
- `data/generated/` - Données générées (recettes, scrapes, etc.)
- `schemas/` - Schémas de données

## Couches à trier avant réutilisation

### Conserver presque telles quelles

- Règles de gouvernance génériques (`generic-domain.md`)
- Workflows de cadrage, diagnostic, nettoyage et hygiène
- Décisions expliquant le modèle opératoire Windsurf
- Structure de répertoires canonique
- `.gitignore` configuré pour les environnements de développement

### Adapter systématiquement

- `README.md` - Description du nouveau projet, installation, usage
- `AGENTS.md` - Objectif, zones canoniques, contraintes du nouveau domaine
- `CONTRIBUTING.md` - Workflow de développement spécifique au projet
- Règles métier spécifiques au domaine (ex: `mealie-domain.md`)
- Skills semi-transverses contenant un vocabulaire produit spécifique
- `.github/workflows/` - Adapter les workflows GitHub Actions si nécessaire

### Retirer si non pertinents

- Workflows uniquement utiles au domaine source
- Skills purement métier du projet source
- Scripts historiques qui ne servent pas le nouveau repo
- Données d'exemple, rapports et artefacts générés
- Addons et packages spécifiques au domaine source
- Fichiers temporaires et artefacts de développement

## Principes de gouvernance

### Source de vérité unique

- Une capacité métier ne doit pas exister dans plusieurs fichiers concurrents
- Si une capacité existe déjà dans un module, modifier ce module au lieu de créer une variante
- Les scripts servent d'orchestrateurs ou d'outils ponctuels, pas de source de vérité métier

### Catégorisation des fichiers

- **Canonique** : `addons/`, `packages/`, `tests/`, `docs/`, `scripts/`
- **Exploratoire** : `labs/`
- **Temporaire** : `tmp/`
- **Généré** : `reports/` ou `data/generated/`

### Règles de nommage

- Ne pas créer de nouveau fichier métier à la racine
- Ne pas utiliser `final`, `final2`, `debug`, `copy`, `backup`, `new`, `fixed`, `v2`, `v3` dans les noms
- Ne pas dupliquer un fichier existant pour tester une hypothèse
- Toute expérimentation utile doit être promue dans le module canonique ou supprimée

### Intégration externe

- Pour les opérations sur des services externes, préférer les MCP disponibles avant d'écrire une logique ad hoc
- Les intégrations doivent rester externes et passer par des interfaces publiques
- Aucun secret, token ou URL sensible ne doit être hardcodé dans le code versionné

### Modes Windsurf

- **Ask mode** : Cadrage, diagnostic, arbitrage
- **Plan mode** : Nouveau module, refactor, gouvernance, changement non trivial
- **Code mode** : Implémentation après cadrage suffisant
- **Worktree mode** : Changements risqués, réorganisation de repo, expérimentation structurée

## Procédure minimale de bootstrap

1. **Copier le noyau de gouvernance** : AGENTS.md, .windsurf/, docs/specs/, docs/decisions/
2. **Réécrire README.md** pour le nouveau projet (description, installation, usage)
3. **Adapter AGENTS.md** avec l'objectif, les zones canoniques et les contraintes du nouveau domaine
4. **Garder les Rules génériques** et remplacer la règle métier par une règle du nouveau domaine si nécessaire
5. **Conserver les workflows génériques** et supprimer ceux qui ne s'appliquent pas
6. **Conserver les skills transverses** et supprimer les skills métier non pertinents
7. **Adapter CONTRIBUTING.md** avec le workflow de développement spécifique au projet
8. **Vérifier l'absence de fichiers racine parasites** (fichiers temporaires, artefacts)
9. **Nettoyer les répertoires** : tmp/, reports/, data/generated/ doivent être vides ou ignorés
10. **Documenter la première décision d'architecture** du nouveau repo dans `docs/decisions/`
11. **Configurer les workflows GitHub Actions** si nécessaire (CI, CodeQL, etc.)

## Critères de réussite

- Le nouveau repo est compréhensible dès la lecture du `README.md`
- La hiérarchie `AGENTS.md` / `Rules` / `Workflows` / `Skills` est explicite
- Aucune dette métier du repo source n'est copiée par inertie
- La structure du repo reste propre et extensible
- Les fichiers temporaires et artefacts sont correctement ignorés
- Les workflows de contribution sont clairs et documentés
- La sécurité (secrets, tokens) est correctement gérée
