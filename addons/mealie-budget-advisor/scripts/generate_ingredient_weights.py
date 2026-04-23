"""Script pour générer une base de données de poids moyens via IA.

Ce script utilise l'IA pour générer une base de poids moyens pour les
ingrédients courants, qui sera ensuite stockée localement et utilisée
sans appels IA ultérieurs.
"""

import json
import logging
import os
from typing import Dict, Optional

import requests

# Configuration
OUTPUT_FILE = "../src/mealie_budget_advisor/pricing/ingredient_weights_ia.json"
COMMON_INGREDIENTS = [
    # Légumes
    "courgette", "tomate", "oignon", "ail", "poivron", "aubergine", "carotte",
    "pomme de terre", "patate", "brocoli", "chou", "concombre", "épinard",
    "salade", "poireau", "asperge", "haricot vert", "petit pois", "champignon",
    "radis", "betterave", "céleri", "fenouil", "endive", "courge", "potiron",
    
    # Fruits
    "pomme", "poire", "banane", "orange", "citron", "pêche", "abricot",
    "fraise", "framboise", "myrtille", "raisin", "kiwi", "mangue", "ananas",
    
    # Viandes
    "poulet", "dinde", "canard", "bœuf", "veau", "agneau", "porc",
    "côte de porc", "escalope de poulet", "steak", "saucisse", "lardon",
    
    # Poissons
    "saumon", "thon", "cabillaud", "crevette", "moule", "coquille",
    
    # Produits laitiers
    "œuf", "fromage", "beurre", "crème", "yaourt", "lait",
    
    # Féculents
    "pain", "pâtes", "riz", "farine", "quinoa", "semoule",
    
    # Herbes et épices
    "basilic", "persil", "thym", "romarin", "laurier", "cumin", "paprika",
    "curry", "gingembre", "cannelle", "poivre", "sel", "muscade",
    
    # Huiles et condiments
    "huile d'olive", "huile de tournesol", "vinaigre", "moutarde", "ketchup",
    "mayonnaise", "soja", "sauce soja",
    
    # Autres
    "chocolat", "sucre", "miel", "levure", "bicarbonate", "vanille",
]


def generate_weights_with_openai(ingredients: list[str], api_key: str, model: str = "gpt-4o-mini") -> Dict[str, float]:
    """Génère les poids moyens via OpenAI API.
    
    Args:
        ingredients: Liste des ingrédients
        api_key: Clé API OpenAI
        model: Modèle à utiliser
        
    Returns:
        Dictionnaire {ingrédient: poids_moyen_kg}
    """
    prompt = f"""Génère le poids moyen en kilogrammes pour une unité/pièce de chaque ingrédient suivant.
Retourne uniquement un JSON valide avec le format: {{"ingrédient": poids_en_kg}}.
Pour les ingrédients très légers (épices, herbes), utilise des valeurs comme 0.001, 0.002, etc.
Pour les légumes moyens, utilise ~0.1-0.3kg.
Pour les viandes, utilise ~0.15-0.25kg par pièce.
Pour les fruits, utilise ~0.1-0.2kg.

Ingrédients: {', '.join(ingredients)}"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Tu es un expert en cuisine et nutrition. Tu fournis des estimations de poids réalistes pour les ingrédients."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"}
    }
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        weights = json.loads(content)
        
        return weights
    except Exception as e:
        logging.error(f"Erreur génération IA: {e}")
        raise


def generate_weights_with_anthropic(ingredients: list[str], api_key: str, model: str = "claude-3-haiku-20240307") -> Dict[str, float]:
    """Génère les poids moyens via Anthropic API.
    
    Args:
        ingredients: Liste des ingrédients
        api_key: Clé API Anthropic
        model: Modèle à utiliser
        
    Returns:
        Dictionnaire {ingrédient: poids_moyen_kg}
    """
    prompt = f"""Génère le poids moyen en kilogrammes pour une unité/pièce de chaque ingrédient suivant.
Retourne uniquement un JSON valide avec le format: {{"ingrédient": poids_en_kg}}.
Pour les ingrédients très légers (épices, herbes), utilise des valeurs comme 0.001, 0.002, etc.
Pour les légumes moyens, utilise ~0.1-0.3kg.
Pour les viandes, utilise ~0.15-0.25kg par pièce.
Pour les fruits, utilise ~0.1-0.2kg.

Ingrédients: {', '.join(ingredients)}"""

    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    data = {
        "model": model,
        "max_tokens": 4096,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()
        content = result["content"][0]["text"]
        weights = json.loads(content)
        
        return weights
    except Exception as e:
        logging.error(f"Erreur génération IA: {e}")
        raise


def generate_weights_with_ai(ingredients: list[str]) -> Dict[str, float]:
    """Génère les poids moyens via IA.
    
    Args:
        ingredients: Liste des ingrédients
        
    Returns:
        Dictionnaire {ingrédient: poids_moyen_kg}
    """
    provider = os.getenv("AI_PROVIDER", "openai")
    api_key = os.getenv("AI_API_KEY")
    model = os.getenv("AI_MODEL", "gpt-4o-mini")
    
    if not api_key:
        raise ValueError("AI_API_KEY non définie dans les variables d'environnement")
    
    if provider == "openai":
        return generate_weights_with_openai(ingredients, api_key, model)
    elif provider == "anthropic":
        return generate_weights_with_anthropic(ingredients, api_key, model)
    else:
        raise ValueError(f"Provider IA non supporté: {provider}")


def save_weights_to_file(weights: Dict[str, float], output_file: str) -> None:
    """Sauvegarde les poids dans un fichier JSON."""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(weights, f, indent=2, ensure_ascii=False)
    print(f"Poids sauvegardés dans {output_file}")


def main():
    """Fonction principale."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Génération des poids moyens via IA...")
    weights = generate_weights_with_ai(COMMON_INGREDIENTS)
    
    logger.info(f"{len(weights)} poids générés")
    save_weights_to_file(weights, OUTPUT_FILE)


if __name__ == "__main__":
    main()
