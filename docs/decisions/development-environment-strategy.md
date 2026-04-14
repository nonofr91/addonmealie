# Development Environment Strategy

## Contexte

Le projet vise à construire des addons externes autour de Mealie sans modifier son image.

Mealie est actuellement déployé en production via Coolify auto-hébergé en utilisant le template Docker officiel.

Cette contrainte soulève une question structurante pour le développement : faut-il itérer directement dans Coolify, ou reproduire Mealie localement pour les tests de développement.

## Décision

Le développement courant doit s'appuyer en priorité sur un environnement local Docker reproduisant Mealie au plus près.

Coolify reste l'environnement de validation d'intégration et de déploiement, et non la boucle principale de développement.

Le modèle cible du projet distingue trois niveaux d'environnement :

- local pour le développement et les tests rapides
- validation plateforme dans Coolify pour vérifier packaging, réseau, configuration et runtime réel
- production après validation locale et validation Coolify

## Rationale

### Vitesse d'itération

- le développement local permet des boucles de test plus courtes
- le debugging, le reset de données et l'observation des logs sont plus simples en local
- il évite de transformer chaque changement en opération de build et de déploiement distant

### Réalisme d'exploitation

- Coolify reste la référence pour le runtime réel des addons déployés
- certains problèmes n'apparaissent qu'avec le réseau, les secrets, les commandes et les volumes du runtime conteneurisé
- la validation dans Coolify reste indispensable avant toute promotion vers un environnement stable

### Réduction du risque

- le développement local limite l'impact des essais sur une instance plus durable
- il réduit le risque de polluer l'environnement Coolify avec des itérations incomplètes
- il facilite l'expérimentation tout en gardant Coolify comme point de vérification final

## Contraintes retenues

### Environnement local

- un Mealie local Docker doit servir de base aux tests d'intégration de développement
- les addons doivent pouvoir être exécutés localement contre cette instance
- les configurations locales doivent rester externalisées et sans secret versionné

### Environnement Coolify

- Coolify sert à valider le packaging conteneur, les variables d'environnement, les secrets, le réseau et le comportement réel du runtime
- les addons déployés dans Coolify restent des services séparés du conteneur Mealie
- un addon ne doit pas dépendre d'un accès interne au conteneur Mealie pour fonctionner

### Promotion entre environnements

- un changement significatif doit d'abord être vérifié localement
- un addon destiné au déploiement doit ensuite être validé dans Coolify
- la production ne doit pas servir de terrain principal de développement ou de diagnostic initial

## Conséquences

- le repo doit tendre vers une expérience de test locale reproductible avec Docker
- les addons doivent être conçus pour fonctionner à la fois en local et dans un runtime conteneurisé Coolify
- les choix de développement doivent éviter les dépendances implicites à un environnement unique
- la documentation des addons devra distinguer clairement les instructions locales et les instructions de validation Coolify
- `mealie-import-orchestrator` doit être testé localement contre un Mealie Docker avant d'être validé comme job ou cron dans Coolify
