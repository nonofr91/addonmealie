# Guide de déploiement GitHub pour mealie-nutrition-advisor

Ce document décrit les précautions d'usage pour le déploiement de l'addon nutrition sur GitHub avant le déploiement sur Coolify.

## Précautions de sécurité

### Secrets et clés API

- **NE JAMAIS** commit de clés API dans le repo
- Utiliser des variables d'environnement pour tous les secrets
- Le fichier `.env` est dans `.gitignore` et ne doit pas être commité
- Le fichier `.env.template` contient les variables sans valeurs sensibles

### Variables d'environnement requises pour Coolify

- `MEALIE_API_KEY` : Token API Mealie (obligatoire)
- `ADDON_SECRET_KEY` : Secret pour auth API entre services (recommandé)
- `ENABLE_NUTRITION` : Activer l'intégration avec mealie-import-orchestrator (défaut: `true`)
- `AI_PROVIDER` : Provider IA (défaut: `mock`)
- `USE_AI_ESTIMATION` : Activer l'estimation IA des quantités (défaut: `false`)

### Fichiers sensibles protégés par .gitignore

- `.env` : Configuration locale avec secrets
- `.venv/` : Environnement virtuel local
- `.pytest_cache/` : Cache pytest
- `data/nutrition_cache.json` : Cache nutrition local
- `data/menu_plans/` : Plans de menu locaux

## Structure du repo

```
addons/mealie-nutrition-advisor/
├── .env.template          # Template de configuration (sans secrets)
├── .gitignore             # Protection des fichiers sensibles
├── Dockerfile             # Image Docker
├── docker-compose.yml     # Déploiement Docker local
├── README.md              # Documentation utilisateur
├── pyproject.toml         # Configuration Python
├── src/
│   └── mealie_nutrition_advisor/
│       ├── config.py      # Configuration centralisée
│       ├── api.py         # API FastAPI
│       ├── ui.py          # UI Streamlit
│       ├── orchestrator.py# CLI
│       └── ...
└── tests/                 # Tests unitaires
```

## Checklist avant commit GitHub

- [ ] Vérifier qu'aucun secret n'est dans le code
- [ ] Vérifier que `.env` n'est pas commité
- [ ] Vérifier que `.gitignore` est à jour
- [ ] Tester l'installation locale `pip install -e .`
- [ ] Tester l'API `python -m mealie_nutrition_advisor.api`
- [ ] Tester l'UI `python -m mealie_nutrition_advisor.ui`
- [ ] Vérifier que Docker build fonctionne
- [ ] Mettre à jour README.md avec les dernières modifications
- [ ] Vérifier que pyproject.toml est à jour avec les dépendances

## Processus de déploiement

### 1. Commit des modifications

```bash
git add addons/mealie-nutrition-advisor/
git commit -m "feat(nutrition): add API and UI integration"
git push
```

### 2. Configuration Coolify

Dans Coolify, configurer les variables d'environnement :
- `MEALIE_API_KEY` : Token API Mealie
- `ADDON_SECRET_KEY` : Secret pour auth API
- `ENABLE_NUTRITION=true`
- `AI_PROVIDER=mock` (ou autre provider)
- `USE_AI_ESTIMATION=false`

### 3. Build Docker sur Coolify

Le service nutrition-api utilisera le Dockerfile de l'addon nutrition pour build l'image.

## Intégration avec mealie-import-orchestrator

Le service nutrition-api est déjà intégré dans `docker-compose.coolify.yml` :

- Dépendance sur mealie avec condition `service_healthy`
- Communication via réseau Docker interne
- Appel automatique depuis mealie-import-orchestrator via `NUTRITION_API_URL`

## Support et maintenance

- Pour les bugs : Créer une issue GitHub
- Pour les questions : Vérifier README.md
- Pour les mises à jour : Suivre le changelog dans README.md
