# Guide de gouvernance pour les agents Cascade

Ce dépôt sert à construire des améliorations externes pour Mealie.

## Objectif du dépôt

- **Ne jamais modifier l'image Mealie**
- **Construire des addons externes** : MCP, workers, pipelines d'import, normalisation, audit, nutrition, images
- **Garder un repo propre** : pas de prolifération de scripts `final_*`, `debug_*`, `copy`, `v2`
- **Conserver une seule source de vérité** par capacité métier

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

---
*Ce dépôt doit évoluer vers une plateforme d'addons externes pour Mealie, maintenable, publiable et sans pollution structurelle, et servir de starter pack Windsurf réutilisable pour d'autres projets.*
