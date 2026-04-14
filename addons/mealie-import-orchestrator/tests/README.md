# Tests - Mealie Import Orchestrator

Ce dossier contient les validations automatisées minimales de l'addon.

## Test disponible

- `test_cli_smoke.py` : vérifie que la commande `status` renvoie un JSON exploitable dans un contexte local de monorepo
- `fixtures/structured_recipe.json` : recette structurée versionnée pour tester localement `step importing` contre une instance Mealie de développement
