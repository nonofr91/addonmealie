# Local Mealie Dev Stack Spec

## But

Définir une stack locale Docker simple et reproductible pour développer et tester les addons externes autour de Mealie sans dépendre de Coolify à chaque itération.

## Problème traité

La stratégie d'environnements du projet impose un développement principal en local Docker, puis une validation dans Coolify.

Il faut donc une stack locale canonique, légère et stable, qui permette de tester l'intégration des addons contre une instance Mealie locale.

## Portée

La première version de la stack locale couvre :

- une instance Mealie locale lancée via Docker Compose
- une configuration externalisée par fichier `.env`
- un réseau et un volume dédiés au développement local
- un point de départ simple pour brancher les addons depuis l'hôte ou depuis un conteneur séparé

## Non-objectifs

- reproduire intégralement l'environnement Coolify
- embarquer les addons dans le même conteneur que Mealie
- devenir une stack de production
- dépendre de secrets versionnés

## Source de vérité

La stack locale canonique doit vivre dans `packages/mealie-dev-stack/`.

## Usage visé

- lancer rapidement un Mealie local pour les tests d'intégration
- exécuter un addon localement contre cette instance
- valider ensuite le packaging et le runtime réel dans Coolify

## Contraintes

- utiliser l'image officielle Mealie
- garder la configuration locale simple et externalisée
- éviter les dépendances implicites à Coolify
- permettre un reset facile des données locales

## Validations attendues

- un `docker-compose.yml` minimal et lisible
- un `.env.template` sans secret
- une documentation courte expliquant le rôle de la stack
- un chemin canonique unique pour éviter la prolifération de variantes Docker locales
