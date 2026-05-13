# Mealie Menu Orchestrator

**Addon externe** pour coordonner les fonctions de Nutrition et Budget dans la création de menus multi-critères.

## Périmètre

- Coordination entre Nutrition Advisor et Budget Advisor
- Génération de menus hebdomadaires avec scoring combiné
- Workflow en deux temps : génération du menu → définition des quantités
- Intégration avec le planning natif Mealie
- API REST pour la génération et la gestion des menus
- UI unifiée Streamlit
- Algorithme de variété basé sur l'historique des menus

## Architecture

```
addons/mealie-menu-orchestrator/
  src/mealie_menu_orchestrator/
    api.py              # API REST FastAPI
    config.py           # Configuration
    orchestrator.py     # Logique d'orchestration
    models/             # Pydantic models
      menu.py
    clients/            # Clients externes
      mealie_client.py
      nutrition_client.py
      budget_client.py
    scoring/            # Moteur de scoring
      combined_scorer.py
```

## Critères de scoring

L'addon évalue les recettes selon 4 critères avec des poids configurables :

- **Nutrition** : Score du Nutrition Advisor (protéines, calories équilibrées)
- **Budget** : Coût normalisé inverse (coût faible = score élevé)
- **Variété** : Basé sur l'historique des menus (évite les répétitions)
- **Saisonnalité** : Tags saison (optionnel)

Formule :
```
Score = w1 * nutrition + w2 * budget + w3 * variété + w4 * saison
```

Par défaut : w1 = w2 = w3 = w4 = 0.25

## Installation

### Développement local

```bash
cd addons/mealie-menu-orchestrator
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### Configuration

Copier `.env.template` vers `.env` et configurer les variables :

```bash
cp .env.template .env
# Éditer .env avec vos URLs et clés API
```

### Démarrage

```bash
# API
python3 -m mealie_menu_orchestrator.api

# CLI
mealie-menu --start-date 2026-01-01 --end-date 2026-01-07 --budget 200 --push
```

## API REST

### Endpoints

- `GET /health` - Health check
- `GET /config` - Configuration actuelle
- `POST /menus/generate` - Générer un menu
- `GET /menus/{id}` - Récupérer un menu
- `POST /menus/{id}/quantities` - Mettre à jour les quantités
- `POST /menus/{id}/push-to-mealie` - Pousser vers Mealie

### Exemple de requête

```bash
curl -X POST http://localhost:8004/menus/generate \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2026-01-01",
    "end_date": "2026-01-07",
    "budget_limit": 200.0,
    "priorities": {
      "nutrition": 0.3,
      "budget": 0.3,
      "variety": 0.2,
      "season": 0.2
    }
  }'
```

## Dépendances

- Nutrition Advisor (API sur port 8001)
- Budget Advisor (API sur port 8003)
- Mealie (API avec clé d'accès)

## Déploiement Docker

```bash
docker build -t mealie-menu-orchestrator:latest .
docker run -p 8004:8004 --env-file .env mealie-menu-orchestrator:latest
```

## Workflow utilisateur

1. Définir la période (semaine)
2. Configurer les critères (priorités, budget)
3. Générer automatiquement OU explorer manuellement
4. Ajuster le menu (remplacer des recettes)
5. Définir les quantités par repas
6. Pousser vers le planning Mealie

## Roadmap

- [x] Structure de l'addon
- [x] Moteur de scoring combiné
- [x] API REST de base
- [x] Stockage des menus (in-memory)
- [x] UI Streamlit unifiée
- [x] Algorithme de variété amélioré
- [x] Documentation de déploiement
- [x] Tests de base
- [ ] Stockage persistant des menus (SQLite/PostgreSQL)
- [ ] Intégration saisonnalité (tags saison)
- [ ] Tests E2E complets
- [ ] Monitoring et logs

---

*Cet addon ne modifie pas l'image Mealie et passe exclusivement par les interfaces publiques API.*
