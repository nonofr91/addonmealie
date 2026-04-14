# Mealie Dev Stack

Cette stack fournit une instance locale Docker de Mealie pour développer et tester les addons du repo.

## Usage

1. Copier `.env.template` vers `.env`
2. Lancer `docker compose up -d`
3. Utiliser l'instance locale Mealie pour les tests d'intégration des addons
4. Pour le premier addon canonique, consulter `addons/mealie-import-orchestrator/README.md`
5. Pour le parcours complet recommandé, consulter `docs/specs/local-addon-dev-flow.md`

## Portée

Cette stack sert au développement local.

Elle ne remplace pas la validation finale dans Coolify.
