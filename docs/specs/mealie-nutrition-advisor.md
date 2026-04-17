# Spec — mealie-nutrition-advisor

**Addon externe** permettant de calculer les valeurs nutritionnelles des recettes Mealie et de générer des menus personnalisés par profil de foyer.

---

## Périmètre

- Calcul des macronutriments (kcal, protéines, lipides, glucides, fibres, sel) par ingrédient puis par recette/portion
- Gestion des profils des membres du foyer avec calcul BMR/TDEE et objectifs personnalisés
- Enrichissement batch des recettes Mealie (PATCH champ `nutrition` via MCP)
- Planification de menus hebdomadaires compatibles avec les profils et restrictions

## Hors périmètre

- Modification de l'image Mealie
- Calcul des micronutriments (vitamines, minéraux) — phase future
- Interface web (CLI uniquement pour cette version)

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
Cibles numériques : `protein_g_per_day`, `max_fat_pct`, `max_calories_per_day`  
Calcul : BMR Mifflin-St Jeor → TDEE (× PAL) → répartition macros OMS  

## Contrat MCP / Mealie

- **Lecture** : `mcp3_get_recipes`, `mcp3_get_recipe_detailed`
- **Écriture** : `mcp3_update_recipe` pour patcher le champ `nutrition`
- **Planning** : `mcp3_create_mealplan_bulk`
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

- `httpx>=0.27` — client HTTP async pour OFF
- `pydantic>=2.0` — modèles et validation
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
```

---

*Cet addon ne modifie pas l'image Mealie et passe exclusivement par les interfaces publiques MCP/API.*
