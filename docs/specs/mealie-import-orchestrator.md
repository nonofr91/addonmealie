# Mealie Import Orchestrator Spec

## But

Définir le premier addon concret du repo sous la forme d'un orchestrateur externe capable de piloter le workflow d'import de recettes vers Mealie.

## Problème traité

Le repo dispose déjà d'un pipeline technique dans `mealie-workflow/` pour enchaîner le scraping, la structuration et l'import.

En revanche, il manque encore un addon canonique dans `addons/` qui transforme cette capacité en point d'entrée produit clair, publiable et réutilisable.

## Positionnement

Le futur module `addons/mealie-import-orchestrator/` a pour rôle d'orchestrer un cas d'usage métier stable.

Il ne remplace ni `mealie-workflow/` ni `mealie-mcp-server/`.

## Responsabilité

La responsabilité de cet addon est de fournir une couche d'orchestration pour l'import de recettes dans Mealie, avec une configuration explicite, des validations d'exécution et des sorties lisibles.

## Périmètre v1

La première version couvre :

- le déclenchement du workflow complet `scraping -> structuration -> import`
- le déclenchement d'une étape unique si nécessaire
- la validation des paramètres d'entrée et de la configuration
- la restitution d'un état d'exécution cohérent
- l'exposition des rapports produits par le workflow existant

## Non-objectifs

- réimplémenter la logique de scraping, structuration ou import
- remplacer le serveur MCP canonique
- créer une interface Mealie alternative
- ajouter des écritures directes hors des interfaces déjà utilisées par les modules canoniques

## Dépendances canoniques

- `mealie-workflow/` reste la source de vérité pour le workflow et ses étapes
- `mealie-mcp-server/` reste la source de vérité pour les opérations MCP et l'accès structuré à Mealie
- `docs/decisions/mealie-platform-constraints.md` fixe les contraintes plateforme
- `docs/specs/mealie-addon-contract.md` fixe le contrat générique d'addon

## Cas d'usage prioritaires

### Workflow complet

- lancer une importation complète à partir de sources configurées
- récupérer le résultat global, le statut et le rapport généré

### Exécution ciblée

- lancer uniquement `scraping`
- lancer uniquement `structuring` sur un fichier déjà produit
- lancer uniquement `importing` sur un fichier structuré existant

### Pilotage et suivi

- récupérer le statut d'une exécution
- exposer les fichiers produits et les statistiques principales
- fournir un message final compréhensible par un humain ou un orchestrateur externe

## Entrées

- configuration Mealie externalisée
- configuration des sources d'import
- mode d'exécution : complet ou par étape
- paramètres de ciblage éventuels : sources, fichier scraped, fichier structured

## Sorties

- résultat d'exécution structuré
- statut de progression
- statistiques de traitement
- chemins des artefacts générés par le workflow
- message final exploitable

## Effets de bord

Les effets de bord sont limités à ceux déjà portés par le workflow canonique et par les interfaces publiques de Mealie :

- scraping de sources externes
- production de fichiers intermédiaires et de rapports
- création de recettes dans Mealie via la couche canonique existante

## Frontières de responsabilité

### Ce que l'addon fait

- valider l'entrée utilisateur
- choisir le bon mode d'exécution
- appeler le workflow canonique
- reformater et exposer le résultat de manière stable

### Ce que l'addon ne fait pas

- parser lui-même les recettes web
- transformer lui-même les données au format Mealie
- appeler une implémentation non canonique du MCP
- devenir la nouvelle source de vérité métier du pipeline

## Point d'entrée visé

Le futur addon doit vivre dans `addons/mealie-import-orchestrator/` avec un point d'entrée unique et documenté.

La forme exacte peut être une CLI en première version, avec possibilité d'évolution vers un service ou un worker si cela devient utile.

## Risques

- couplage direct à des scripts historiques au lieu du workflow canonique
- confusion entre orchestration produit et logique métier de pipeline
- exposition de détails internes des fichiers produits comme contrat public trop rigide
- multiplication de modes d'entrée sans validation stricte

## Validations attendues

- un seul point d'entrée d'addon identifié dans `addons/`
- aucun code métier dupliqué depuis `mealie-workflow/`
- dépendances explicites vers les modules canoniques
- configuration externalisée et validée avant exécution
- au moins un scénario testé pour le workflow complet
- au moins un scénario testé pour une exécution par étape
