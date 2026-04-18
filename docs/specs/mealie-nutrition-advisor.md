# Spec — mealie-nutrition-advisor

**Addon externe** permettant de calculer les valeurs nutritionnelles des recettes Mealie et de générer des menus personnalisés par profil de foyer.

---

## Périmètre

- Calcul des macronutriments (kcal, protéines, lipides, glucides, fibres, sel) par ingrédient puis par recette/portion
- Gestion des profils des membres du foyer avec calcul BMR/TDEE et objectifs personnalisés
- **Profils avancés** : pathologies médicales (diabetes, hypertension, gout, etc.) avec ajustement des cibles nutritionnelles
- **Présences hebdomadaires** : pattern de présence par jour et repas pour ajuster les portions et le planning
- Enrichissement batch des recettes Mealie (PATCH champ `nutrition` via API REST)
- Planification de menus hebdomadaires compatibles avec les profils, restrictions et pathologies
- **Intégration planning natif Mealie** : utilisation de `recipe_id` (UUID) pour créer des entrées mealplan
- **API FastAPI** : endpoints REST pour gestion des profils et présence hebdomadaire
- **UI Streamlit** : interface web pour gestion des profils et enrichissement nutritionnel

## Hors périmètre

- Modification de l'image Mealie
- Calcul des micronutriments (vitamines, minéraux) — phase future

---

## Architecture

```
addons/mealie-nutrition-advisor/
  src/mealie_nutrition_advisor/
    models/           # Pydantic models (nutrition, profile, menu)
    nutrition/        # Moteur de calcul (OFF API + LLM fallback + cache)
    profiles/         # Gestion profils foyer + BMR/TDEE
    planner/          # Score, filtre, planificateur hebdo
    mealie_sync.py    # PATCH Mealie via MCP/REST
    orchestrator.py   # CLI entry point
```

## Sources de données nutritionnelles

1. **Open Food Facts** (priorité) — API publique gratuite, sans clé, base mondiale
2. **LLM fallback** (si OFF ne retourne rien) — prompt structuré → JSON nutrition
3. **Cache JSON local** — `data/nutrition_cache.json`, TTL configurable (défaut 30 jours)

## Profil membre du foyer

Champs : `name`, `age`, `sex`, `weight_kg`, `height_cm`, `activity_level`  
Objectifs : `goal` (perte/maintien/prise), `restrictions` (allergies, régimes)  
**Pathologies médicales** : `medical_conditions` (diabetes, hypertension, gout, gerd, kidney_disease, high_cholesterol)  
**Présence hebdomadaire** : `weekly_presence` pattern par jour et repas (breakfast/lunch/dinner)  
Cibles numériques : `protein_g_per_day`, `max_fat_pct`, `max_calories_per_day`  
Calcul : BMR Mifflin-St Jeor → TDEE (× PAL) → répartition macros OMS  
**Ajustements pathologies** : sodium réduit pour hypertension/kidney_disease, glucides limités pour diabetes  

## Contrat Mealie (API REST)

**Décision d'architecture** : L'addon utilise l'API REST directe de Mealie pour maintenir son autonomie comme service Docker indépendant. Voir `docs/decisions/nutrition-addon-mcp-vs-rest.md`.

- **Lecture** : GET `/api/recipes`, GET `/api/recipes/{slug}`
- **Écriture** : PATCH `/api/recipes/{slug}` pour le champ `nutrition`
- **Planning** : POST `/api/households/mealplans` avec `recipe_id` (UUID) ou `title`
- Pas de modification directe en base Mealie

## Stockage

| Données | Fichier | Nature |
|---|---|---|
| Profils foyer | `config/household_profiles.json` | Versionnable |
| Cache nutrition | `data/nutrition_cache.json` | Généré, ignoré par git |
| Rapports planning | `data/menu_plans/` | Généré |

## Commandes CLI

```bash
mealie-nutrition enrich          # Enrichit toutes les recettes sans nutrition
mealie-nutrition enrich --force  # Réenrichit toutes les recettes
mealie-nutrition profile list    # Affiche les profils du foyer
mealie-nutrition profile add     # Ajoute un membre interactif
mealie-nutrition plan --week 2026-W16  # Génère menu semaine
mealie-nutrition plan --push     # Pousse le menu dans Mealie
```

## Dépendances

- `httpx>=0.27` — client HTTP async pour OFF et Mealie
- `pydantic>=2.0` — modèles et validation
- `fastapi>=0.100` — API REST pour gestion des profils
- `uvicorn>=0.20` — serveur ASGI pour FastAPI
- `streamlit>=1.30` — interface web pour gestion des profils
- `requests>=2.30` — client HTTP pour Streamlit → API
- `openai>=1.0` ou `anthropic>=0.20` — LLM fallback (optionnel)
- `python-dotenv>=1.0` — config via env

## Variables d'environnement requises

```bash
MEALIE_BASE_URL        # URL de l'instance Mealie
MEALIE_API_KEY         # Token API Mealie
AI_PROVIDER            # openai | anthropic | mock (défaut: mock)
OPENAI_API_KEY         # Si AI_PROVIDER=openai
ANTHROPIC_API_KEY      # Si AI_PROVIDER=anthropic
OFF_BASE_URL           # Défaut: https://world.openfoodfacts.org/api/v2
NUTRITION_CACHE_TTL_DAYS  # Défaut: 30

# API FastAPI
ADDON_API_HOST         # Défaut: 0.0.0.0
ADDON_API_PORT         # Défaut: 8001
ADDON_SECRET_KEY       # Clé pour authentification API (optionnel)

# UI Streamlit
ADDON_UI_PORT          # Défaut: 8502
ADDON_API_URL          # URL de l'API FastAPI (défaut: http://localhost:8001)
```

---

*Cet addon ne modifie pas l'image Mealie et passe exclusivement par les interfaces publiques MCP/API.*
