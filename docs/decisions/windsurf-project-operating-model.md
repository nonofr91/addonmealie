# Windsurf Project Operating Model

## Objectif

Faire de ce dépôt une base maintenable pour développer des améliorations externes à Mealie avec Cascade, sans pollution structurelle et avec une gouvernance réutilisable sur d'autres projets.

## Couches de pilotage

### AGENTS.md

`AGENTS.md` porte la gouvernance toujours active du repo : objectif du dépôt, règles de création de fichiers, source de vérité, usage des modes Windsurf et checklist de fin de tâche.

### Rules

Les `Rules` dans `.windsurf/rules/` portent les contraintes courtes et durables qui doivent s'activer selon le type de fichier ou le sujet traité.

### Workflows

Les `Workflows` dans `.windsurf/workflows/` servent de runbooks manuels pour les tâches répétables : cadrage d'addon, hygiène du repo, promotion d'expérimentation, nettoyage et préparation de release.

### Skills

Les `Skills` dans `.windsurf/skills/` encapsulent l'expertise métier ou de gouvernance réutilisable avec des descriptions ciblées et, si besoin, des ressources de support.

## Cycle recommandé

1. Qualifier la demande.
2. Identifier la source de vérité.
3. Produire une spec courte si le changement est non trivial.
4. Choisir le bon mode Windsurf.
5. Implémenter dans le module canonique.
6. Valider.
7. Nettoyer les artefacts.
8. Mettre à jour la documentation durable si nécessaire.

## Usage des modes

- `Ask mode` pour cadrer, diagnostiquer et arbitrer.
- `Plan mode` pour les changements non triviaux, multi-fichiers ou structurants.
- `Code mode` pour implémenter après cadrage suffisant.
- `Worktree mode` pour les changements risqués, la réorganisation ou les expérimentations structurées.

## Structure minimale à préserver

- `addons/` pour les addons externes publiables.
- `packages/` pour le code partagé.
- `scripts/` pour l'orchestration stable.
- `tests/` pour les validations.
- `docs/specs/` pour les specs.
- `docs/decisions/` pour les décisions.
- `labs/` pour les expérimentations.
- `tmp/` pour le temporaire.
- `reports/` et `data/generated/` pour le généré.

## Réutilisation comme template

Lorsqu'un nouveau repo est initialisé à partir de ce dépôt, le noyau de gouvernance doit être conservé puis adapté : `AGENTS.md`, `Rules`, workflows génériques, skills transverses, `docs/specs/` et `docs/decisions/`.

Les artefacts trop spécifiques au domaine source doivent être réécrits ou retirés au lieu d'être copiés par inertie.

Le workflow `/bootstrap-project` et la spec `docs/specs/starter-pack-bootstrap.md` servent de procédure canonique pour cette réutilisation.

## Décision

Ce dépôt sert désormais aussi de référence pour un starter pack Windsurf réutilisable, avec une hiérarchie claire entre `AGENTS.md`, `Rules`, `Workflows`, `Skills` et documentation versionnée.
