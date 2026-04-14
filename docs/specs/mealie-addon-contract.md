# Mealie Addon Contract

## But

Définir le contrat minimal que doit respecter tout addon externe développé autour de Mealie dans ce repo.

## Portée

Cette spec s'applique à tout module placé dans `addons/` et destiné à apporter une capacité publiable autour de Mealie.

Elle complète la décision `docs/decisions/mealie-platform-constraints.md` et la spec `docs/specs/mealie-external-addon.md`.

## Principes

- un addon reste externe à Mealie
- un addon a une responsabilité claire
- un addon n'est pas une nouvelle source de vérité pour une capacité déjà canonique
- un addon utilise des interfaces publiques et une configuration externalisée

## Entrées attendues

Tout addon doit expliciter :

- sa configuration d'exécution
- ses paramètres métier d'entrée
- ses dépendances vers `mealie-mcp-server/`, `mealie-workflow/` ou d'autres modules canoniques
- les préconditions nécessaires à son fonctionnement

## Sorties attendues

Tout addon doit produire des sorties explicites, par exemple :

- résultat d'exécution
- rapport de traitement
- état final lisible par un utilisateur, un worker ou un orchestrateur
- journalisation exploitable sans exposition de secrets

## Effets de bord autorisés

Tout addon doit documenter précisément ses effets de bord sur Mealie ou sur le système externe.

Exemples autorisés :

- création ou mise à jour de recettes via interfaces publiques
- enrichissement de métadonnées, catégories, tags ou images
- déclenchement d'un pipeline externe et production de rapports

## Effets de bord interdits

- modification de l'image Mealie
- écriture directe dans la base de données Mealie
- dépendance à des modules internes non publics de Mealie
- duplication de logique déjà canonique dans le MCP ou le pipeline

## Dépendances autorisées

Un addon peut dépendre :

- de `mealie-mcp-server/` pour la couche MCP et l'accès structuré à Mealie
- de `mealie-workflow/` pour les traitements métier déjà existants
- d'un module canonique du repo si sa responsabilité est claire

## Dépendances à éviter

- scripts historiques à la racine
- variantes concurrentes d'une même capacité
- fichiers temporaires ou artefacts générés comme dépendance d'API stable

## Exigences de configuration

- aucun secret versionné
- variables d'environnement ou configuration dédiée pour l'URL Mealie, les tokens et options d'exécution
- validation de la configuration avant toute opération sensible

## Exigences de robustesse

- gestion explicite des erreurs
- timeouts et retries limités sur les appels externes
- idempotence visée pour les opérations relançables
- capacité à produire un état ou un rapport exploitable même en cas d'échec partiel

## Exigences de structure

- un addon vit dans `addons/`
- une responsabilité principale par addon
- une documentation minimale doit décrire le problème traité, le point d'entrée et les dépendances
- les données générées doivent vivre dans les emplacements prévus par la gouvernance du repo

## Checklist de validation

Avant de considérer un addon comme recevable, vérifier :

- qu'il reste externe à Mealie
- qu'il ne duplique pas une capacité déjà canonique
- qu'il explicite ses entrées, sorties et effets de bord
- qu'il utilise une configuration externalisée
- qu'il ne dépend pas d'un script historique racine comme contrat stable
- qu'il peut être compris et publié comme module autonome
