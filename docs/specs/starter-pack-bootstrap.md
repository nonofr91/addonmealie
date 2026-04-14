# Starter Pack Bootstrap Spec

## But

Décrire comment réutiliser ce dépôt comme template de projet sans copier aveuglément son historique métier.

## Périmètre

Cette spec couvre la réutilisation de la couche de gouvernance Windsurf et de la structure canonique du repo.

Elle ne couvre pas la migration automatique des scripts métier existants ni le nettoyage complet de l'historique du projet source.

## Noyau à réutiliser

### Gouvernance

- `AGENTS.md`
- `.gitignore`
- `.windsurf/rules/`
- `.windsurf/workflows/`
- `.windsurf/skills/` pour les expertises transverses
- `docs/specs/`
- `docs/decisions/`

### Structure

- `addons/`
- `packages/`
- `scripts/`
- `tests/`
- `docs/`
- `labs/`
- `tmp/`
- `reports/`
- `data/generated/`

## Couches à trier avant réutilisation

### Conserver presque telles quelles

- règles de gouvernance génériques
- workflows de cadrage, diagnostic, nettoyage et hygiène
- décisions expliquant le modèle opératoire Windsurf

### Adapter systématiquement

- `README.md`
- `AGENTS.md`
- les règles métier spécifiques au domaine
- les skills semi-transverses qui contiennent un vocabulaire produit spécifique

### Retirer si non pertinents

- workflows uniquement utiles au domaine source
- skills purement métier du projet source
- scripts historiques qui ne servent pas le nouveau repo
- données d'exemple, rapports et artefacts générés

## Procédure minimale de bootstrap

1. Copier le noyau de gouvernance.
2. Réécrire `README.md` pour le nouveau projet.
3. Adapter `AGENTS.md` avec l'objectif, les zones canoniques et les contraintes du nouveau domaine.
4. Garder les `Rules` génériques et remplacer la règle métier par une règle du nouveau domaine si nécessaire.
5. Conserver les workflows génériques et supprimer ceux qui ne s'appliquent pas.
6. Conserver les skills transverses et supprimer les skills métier non pertinents.
7. Vérifier l'absence de fichiers racine parasites.
8. Documenter la première décision d'architecture du nouveau repo dans `docs/decisions/`.

## Critères de réussite

- le nouveau repo est compréhensible dès la lecture du `README.md`
- la hiérarchie `AGENTS.md` / `Rules` / `Workflows` / `Skills` est explicite
- aucune dette métier du repo source n'est copiée par inertie
- la structure du repo reste propre et extensible
