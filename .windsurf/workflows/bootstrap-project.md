---
description: Initialiser un nouveau repo à partir de ce starter pack Windsurf sans embarquer la dette métier de ce projet
---

# Workflow Bootstrap Project

Utilise ce workflow quand tu veux réutiliser ce dépôt comme base pour un nouveau projet.

## Objectif

Créer un nouveau repo propre en conservant la gouvernance Windsurf utile et en retirant les couches métier qui ne sont pas pertinentes pour le nouveau domaine.

## Étapes

1. Définir le nouveau contexte de projet : produit, domaine, stack, contraintes, risques.
2. Séparer les artefacts en deux groupes :
   - noyau réutilisable
   - éléments spécifiques au domaine actuel
3. Conserver et adapter en priorité :
   - `AGENTS.md`
   - `.gitignore`
   - `.windsurf/rules/`
   - workflows génériques de gouvernance
   - skills transverses
   - `docs/specs/` et `docs/decisions/`
4. Réécrire ou supprimer les éléments trop spécifiques au domaine source.
5. Mettre à jour `README.md` pour décrire le nouveau projet et son mode opératoire Windsurf.
6. Créer ou adapter une règle métier dédiée dans `.windsurf/rules/` si le nouveau domaine le justifie.
7. Vérifier que la structure canonique est en place : `addons/`, `packages/`, `scripts/`, `tests/`, `docs/`, `labs/`, `tmp/`, `reports/`.
8. Exécuter ensuite `/repo-hygiene` pour confirmer qu'aucune dette structurelle du repo source n'a été embarquée.

## Noyau généralement réutilisable

- `AGENTS.md` comme base de gouvernance, à adapter au nouveau domaine
- `.windsurf/rules/python-files.md`
- `.windsurf/rules/docs-and-governance.md`
- `/task-intake`
- `/bug-investigation`
- `/repo-hygiene`
- `/cleanup-task`
- `/promote-experiment`
- `repo-governance`
- `contract-review`

## Éléments à adapter ou retirer selon le domaine

- `mealie-domain.md`
- les workflows ou skills orientés Mealie
- les modules métier ou scripts historiques du repo source
- toute documentation décrivant un contexte produit devenu faux

## Résultat attendu

Un nouveau repo avec une base Windsurf immédiatement exploitable, mais sans duplication aveugle du contexte métier du projet source.
