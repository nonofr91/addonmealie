# Mealie Addons Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Une suite d'addons externes pour [Mealie](https://mealie.io) qui automatisent les corvées culinaires : import de recettes, calcul nutritionnel, planification de menus, gestion des courses et coaching nutritionnel.

## 🎯 Vision

Devenir l'assistant intelligent ultime pour les corvées culinaires en fournissant des outils modulaires qui s'intègrent à Mealie sans jamais modifier son image Docker.

## ✨ Fonctionnalités

### 🍽️ Import de recettes intelligent
- Scraping de sites de cuisine (Marmiton, 750g, etc.)
- Structuration automatique des recettes
- Audit de qualité (images, tags, doublons)
- Auto-fix avec images de fallback
- Support IA optionnel (OpenAI, Anthropic, Mistral)

### 🥗 Calcul nutritionnel automatique
- Calcul des valeurs nutritionnelles (kcal, protéines, lipides, glucides, fibres)
- Enrichissement des recettes existantes
- Sources multiples : Open Food Facts + IA + cache
- Profils avancés du foyer (pathologies, objectifs)
- Ajustement automatique selon les pathologies médicales

### 📅 Planification de menus
- Génération de menus hebdomadaires
- Adaptation aux profils du foyer
- Gestion des absences (pattern de présence)
- Intégration avec le planning natif Mealie

### 🤖 Intégration MCP
- 45 outils API couvrant l'intégralité de l'API Mealie
- Compatible avec Claude Desktop et autres clients MCP
- Gestion des recettes, listes de courses, catégories, tags

## 🚀 Installation rapide

### Docker (recommandé)

```bash
# Import Addon
docker run -d \
  -e MEALIE_BASE_URL=https://your-mealie.com \
  -e MEALIE_API_KEY=your-key \
  -p 8000:8000 -p 8501:8501 \
  ghcr.io/nonofr91/mealie-import-addon:latest

# Nutrition Addon
docker run -d \
  -e MEALIE_BASE_URL=https://your-mealie.com \
  -e MEALIE_API_KEY=your-key \
  -p 8001:8001 -p 8502:8502 \
  ghcr.io/nonofr91/mealie-nutrition-advisor:latest
```

### Docker Compose

```yaml
services:
  mealie-import-addon:
    image: ghcr.io/nonofr91/mealie-import-addon:latest
    environment:
      - MEALIE_BASE_URL=https://your-mealie.com
      - MEALIE_API_KEY=your-key
    ports:
      - "8000:8000"
      - "8501:8501"

  mealie-nutrition-addon:
    image: ghcr.io/nonofr91/mealie-nutrition-advisor:latest
    environment:
      - MEALIE_BASE_URL=https://your-mealie.com
      - MEALIE_API_KEY=your-key
    ports:
      - "8001:8001"
      - "8502:8502"
```

Voir [docs/INSTALLATION.md](docs/INSTALLATION.md) pour les instructions détaillées.

## 📁 Structure du dépôt

```
.
├── addons/                    # Addons externes Mealie
│   ├── mealie-import-orchestrator/   # Import de recettes
│   ├── mealie-nutrition-advisor/     # Nutrition + menus
│   └── mealie-budget-advisor/        # Budget + estimation coût recettes
├── mealie-mcp-server/         # Serveur MCP pour assistants IA
├── mealie-workflow/           # Scripts et outils d'import
├── packages/                  # Code partagé
├── scripts/                   # Scripts utilitaires
├── docs/                      # Documentation
│   ├── INSTALLATION.md        # Guide d'installation
│   ├── ARCHITECTURE.md        # Architecture technique
│   ├── ROADMAP.md             # Roadmap et perspectives
│   ├── decisions/             # Décisions d'architecture
│   └── internal/              # Documentation interne Windsurf
├── CONTRIBUTING.md            # Guide de contribution
└── LICENSE                    # Licence MIT
```

## 🔧 Addons disponibles

| Addon | Description | API | UI |
|-------|-------------|-----|-----|
| [mealie-import-orchestrator](addons/mealie-import-orchestrator/) | Import de recettes et audit de qualité | :8000 | :8501 |
| [mealie-nutrition-advisor](addons/mealie-nutrition-advisor/) | Calcul nutritionnel et planification | :8001 | :8502 |
| [mealie-budget-advisor](addons/mealie-budget-advisor/) | Budget mensuel + estimation coût des recettes | :8003 | :8503 |
| [mealie-mcp-server](mealie-mcp-server/) | Intégration MCP pour assistants IA | MCP | - |

## 🗺️ Roadmap

Voir [docs/ROADMAP.md](docs/ROADMAP.md) pour les perspectives futures :

- 🔄 Optimisation des listes de courses
- 💰 Budget alimentaire
- ⏱️ Gestion du temps de cuisine
- 🚚 Interface livraison
- 🧠 Coaching nutritionnel personnalisé

## 📚 Documentation

- [Guide d'installation](docs/INSTALLATION.md)
- [Architecture technique](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Contribuer](CONTRIBUTING.md)
- [Décisions d'architecture](docs/decisions/)

## 🤝 Contribuer

Les contributions sont les bienvenues ! Voir [CONTRIBUTING.md](CONTRIBUTING.md) pour les guidelines.

## 📄 Licence

Ce projet est licencié sous la licence MIT - voir le fichier [LICENSE](LICENSE) pour les détails.

## 🙏 Remerciements

- [Mealie](https://github.com/mealie-recipes/mealie) - Le système de gestion de recettes
- [FastMCP](https://github.com/jlowin/fastmcp) - Framework MCP
- [Open Food Facts](https://world.openfoodfacts.org/) - Base de données nutritionnelle

## 🔗 Liens

- [Documentation Mealie](https://docs.mealie.io)
- [MCP Protocol](https://modelcontextprotocol.io)
- [GitHub Issues](https://github.com/nonofr91/addonmealie/issues)
