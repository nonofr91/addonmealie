# Mealie External Addon Spec

## But

Construire un addon externe à Mealie qui réutilise les capacités déjà présentes dans `mealie-mcp-server/` et `mealie-workflow/` pour fournir une couche publiable d’orchestration, d’automatisation et de pilotage.

## Problème traité

Le repo contient déjà des capacités utiles autour de Mealie, mais elles sont réparties entre un serveur MCP canonique et un pipeline métier.

L’objectif n’est pas de créer une application concurrente à Mealie, mais un module externe capable d’exposer ces capacités de manière propre, maintenable et réutilisable.

## Périmètre

La première version de l’addon peut couvrir :

- l’orchestration du pipeline de scraping, structuration et import
- l’appel aux capacités canoniques du serveur MCP Mealie
- la centralisation de la configuration et des validations d’exécution
- l’exposition d’un point d’entrée clair pour des automatisations futures

## Non-objectifs

- modifier l’image Mealie
- dupliquer la logique métier déjà présente dans `mealie-mcp-server/` ou `mealie-workflow/`
- remplacer l’interface native de Mealie
- conserver comme sources actives les variantes historiques à la racine

## Mode d’intégration

L’intégration doit rester externe à Mealie et passer par des interfaces publiques.

L’addon visé est un module dans `addons/` qui orchestre :

- le serveur canonique `mealie-mcp-server/` pour les opérations MCP et Mealie
- le pipeline `mealie-workflow/` pour les traitements métier déjà implémentés

## Entrées

- configuration Mealie par variables d’environnement ou fichiers de config dédiés hors secrets versionnés
- sources de recettes ou paramètres de workflow
- commandes utilisateur, tâches planifiées ou appels d’orchestration

## Sorties

- exécutions de tâches d’import, de structuration ou d’enrichissement
- rapports d’exécution
- résultats exploitables par un utilisateur, un worker ou une interface externe

## Effets de bord

Les effets de bord autorisés sont explicitement ceux réalisés via les interfaces publiques de Mealie :

- création ou mise à jour de recettes
- enrichissement de métadonnées, images, catégories ou tags
- génération de rapports de traitement

## Source de vérité

- `mealie-mcp-server/` reste la source de vérité pour le serveur MCP et les appels Mealie associés
- `mealie-workflow/` reste la source de vérité pour le pipeline de traitement existant
- le futur addon dans `addons/` devient la source de vérité de l’orchestration produit et de l’expérience d’intégration

## Risques

- duplication de logique déjà présente dans les scripts racine ou dans le workflow
- couplage trop fort de l’addon à des scripts historiques non canoniques
- configuration dispersée ou fuite de secrets
- confusion entre rôle du MCP, rôle du pipeline et rôle de l’addon

## Validations attendues

- un point d’entrée d’addon clairement identifié dans `addons/`
- aucune logique métier copiée depuis les modules canoniques
- une documentation qui pointe vers `mealie-mcp-server/` pour le MCP
- une exécution testable de bout en bout sur au moins un cas d’usage prioritaire
- une configuration externalisée sans secret hardcodé
