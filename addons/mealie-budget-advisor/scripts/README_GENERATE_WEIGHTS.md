# Génération de la base de poids moyens via IA

Ce script permet de générer une base de données de poids moyens pour les ingrédients courants en utilisant l'IA une seule fois. Les poids générés sont ensuite stockés localement et utilisés sans appels IA ultérieurs.

## Pourquoi utiliser ce script ?

- **Économie de tokens** : L'IA n'est appelée qu'une seule fois pour générer la base
- **Précision** : L'IA peut fournir des estimations plus précises que les règles manuelles
- **Extensibilité** : Facile d'ajouter de nouveaux ingrédients en régénérant la base

## Prérequis

1. Clé API OpenAI ou Anthropic
2. Python 3.11+
3. Dépendances : `requests`

## Configuration

Ajoutez les variables d'environnement dans votre `.env` :

```bash
AI_PROVIDER=openai  # ou anthropic
AI_API_KEY=sk-...
AI_MODEL=gpt-4o-mini  # ou claude-3-haiku-20240307
```

## Utilisation

```bash
cd scripts
python3 generate_ingredient_weights.py
```

Le script génère un fichier `ingredient_weights_ia.json` dans `src/mealie_budget_advisor/pricing/`.

## Résultat

Le fichier généré est automatiquement chargé par `ingredient_weights.py` s'il existe. Sinon, la base manuelle est utilisée comme fallback.

## Coût estimé

- OpenAI gpt-4o-mini : ~0.01$ pour ~100 ingrédients
- Anthropic claude-3-haiku : ~0.005$ pour ~100 ingrédients
