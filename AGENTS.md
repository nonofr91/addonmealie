# Guide de gouvernance pour les agents Cascade

Ce dépôt sert à construire des améliorations externes pour Mealie.

## Objectif du dépôt

- **Ne jamais modifier l'image Mealie**
- **Construire des addons externes** : MCP, workers, pipelines d'import, normalisation, audit, nutrition, images
- **Garder un repo propre** : pas de prolifération de scripts `final_*`, `debug_*`, `copy`, `v2`
- **Conserver une seule source de vérité** par capacité métier

> **Note** : Pour utiliser ce dépôt comme starter pack Windsurf pour un autre projet, adapter AGENTS.md avec l'objectif, les zones canoniques et les contraintes du nouveau domaine. Voir docs/specs/starter-pack-bootstrap.md pour la procédure de bootstrap.

## Règles de conduite pour Cascade

### 1. Source de vérité

- Si une capacité existe déjà dans un module, il faut modifier ce module au lieu de créer une variante.
- Une capacité métier ne doit pas exister dans plusieurs fichiers concurrents.
- Les scripts servent d'orchestrateurs ou d'outils ponctuels, pas de source de vérité métier.

### 2. Création de fichiers

Avant de créer un fichier, il faut déterminer sa catégorie.

- **Canonique** : `addons/`, `packages/`, `tests/`, `docs/`, `scripts/`
- **Exploratoire** : `labs/`
- **Temporaire** : `tmp/`
- **Généré** : `reports/` ou `data/generated/`

Règles strictes :

- Ne pas créer de nouveau fichier métier à la racine
- Ne pas utiliser `final`, `final2`, `debug`, `copy`, `backup`, `new`, `fixed`, `v2`, `v3` dans les noms de fichiers
- Ne pas dupliquer un fichier existant pour tester une hypothèse
- Toute expérimentation utile doit être promue dans le module canonique ou supprimée

### 3. Mealie et MCP

- Pour les opérations sur Mealie, préférer les MCP disponibles avant d'écrire une logique ad hoc.
- Les intégrations doivent rester externes à Mealie et passer par des interfaces publiques.
- Aucun secret, token ou URL sensible ne doit être hardcodé dans le code versionné.

### 4. Usage des modes Windsurf

- **Ask mode** : cadrage, diagnostic, arbitrage
- **Plan mode** : nouveau module, refactor, gouvernance, changement non trivial
- **Code mode** : implémentation après cadrage suffisant
- **Worktree mode** : changements risqués, réorganisation de repo, expérimentation structurée

### 5. Fin de tâche obligatoire

Avant de conclure une tâche, vérifier :

- qu'aucun fichier parasite n'a été ajouté
- que le changement a été fait au bon endroit
- que les fichiers temporaires ont été supprimés ou isolés
- que la documentation de gouvernance ou la spec a été mise à jour si nécessaire

## Méthodologie de travail

### Cycle standard

1. Qualifier la demande
2. Identifier la source de vérité
3. Écrire une spec courte si le changement est important
4. Planifier les fichiers et validations attendues
5. Implémenter dans le module canonique
6. Valider et nettoyer

### Quand une spec est obligatoire

- Nouveau module ou addon
- Refactor multi-fichiers
- Changement d'architecture
- Pipeline avec effets de bord importants sur Mealie
- Nouvelle règle de gouvernance

## Capacités métier actuelles à préserver

- Import de recettes et pipeline hybride Python + IA
- Normalisation des recettes et ingrédients
- Analyse nutritionnelle
- Optimisation des listes de courses
- Gestion d'images

## Skills et workflows

- Utiliser les skills métier existants quand ils correspondent au besoin
- Utiliser les workflows de gouvernance pour cadrer, nettoyer et promouvoir une expérimentation
- Préférer une règle versionnée dans le repo à une instruction implicite en mémoire
- Utiliser `.windsurf/rules/` pour les contraintes courtes, durables et ciblées par type de fichier ou domaine

## Patterns et erreurs fréquentes à éviter

### Commandes système
- Sur Linux, utiliser `python3` au lieu de `python`
- Dans bash, ne jamais utiliser `cd`, utiliser le paramètre `Cwd`
- Toujours vérifier `git status` avant les opérations destructrices

### Git
- `git mv` ne fonctionne que pour les fichiers versionnés
- Pour les fichiers non versionnés, utiliser `mv` puis `git add`
- Vérifier si un fichier est dans `.gitignore` avant de tenter de le lire

### Release et tags Docker
- **Toujours committer ET pousser AVANT de créer le tag** — le tag doit pointer sur HEAD
- **Séquence obligatoire** : `git add` → `git commit` → `git push` → `git tag` → `git push origin <tag>`
- Ne jamais créer un tag sur un commit intermédiaire si d'autres commits de la même feature sont en attente
- Après un tag, vérifier avec `git log --oneline -3` que le tag pointe bien sur le bon commit
- Le docker-compose doit être mis à jour dans le même commit que le bump de version (pas avant, pas après)

### Packages Python et addons Docker
- **Ne jamais utiliser `sys.path.insert` pour importer un module frère** dans un package installé
- Dans un package installable (`pyproject.toml`, `setup.py`), toujours utiliser des imports relatifs (`from .module import ...`)
- Quand un module est partagé entre `mealie-workflow` et un addon, copier le fichier dans le package addon — c'est la source de vérité dans le conteneur
- Vérifier avec `git status` après un `cp` qu'un nouveau fichier est bien staged avant le commit

### Streamlit en conteneur
- Toujours passer `--server.headless=true --browser.gatherUsageStats=false --server.fileWatcherType=none` dans tout entrypoint Streamlit Docker
- Sans ces flags, Streamlit lance un watcher et un thread de stats qui tentent de rebinder le port → conflit au démarrage
- Ces flags doivent être dans l'entrypoint docker-compose ou le script de lancement, pas dans le code Python

### Gouvernance
- Préférer les MCP disponibles avant d'écrire une logique ad hoc
- Ne jamais hardcoder de secrets, tokens ou URLs sensibles
- Utiliser MCP GitHub pour vérifier l'état distant après les opérations importantes

---
*Ce dépôt doit évoluer vers une plateforme d'addons externes pour Mealie, maintenable, publiable et sans pollution structurelle, et servir de starter pack Windsurf réutilisable pour d'autres projets.*
