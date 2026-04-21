#!/usr/bin/env python3
"""
Module de normalisation des ingrédients pour l'import Mealie
Normalise les noms, traduit en français et standardise les unités
"""

import re
import unicodedata
from typing import Dict, Optional

# Dictionnaire de traduction des ingrédients courants (anglais -> français)
INGREDIENT_TRANSLATIONS = {
    # Légumes
    "tomato": "tomate",
    "tomatoes": "tomates",
    "onion": "oignon",
    "onions": "oignons",
    "garlic": "ail",
    "carrot": "carotte",
    "carrots": "carottes",
    "potato": "pomme de terre",
    "potatoes": "pommes de terre",
    "pepper": "poivron",
    "peppers": "poivrons",
    "cucumber": "concombre",
    "lettuce": "laitue",
    "spinach": "épinard",
    "spinach": "épinards",
    "mushroom": "champignon",
    "mushrooms": "champignons",
    "zucchini": "courgette",
    "eggplant": "aubergine",
    "broccoli": "brocoli",
    "cauliflower": "chou-fleur",
    "celery": "céleri",
    "leek": "poireau",
    "asparagus": "asperge",
    
    # Fruits
    "apple": "pomme",
    "apples": "pommes",
    "banana": "banane",
    "bananas": "bananes",
    "orange": "orange",
    "oranges": "oranges",
    "lemon": "citron",
    "lemons": "citrons",
    "lime": "citron vert",
    "strawberry": "fraise",
    "strawberries": "fraises",
    "blueberry": "myrtille",
    "blueberries": "myrtilles",
    "raspberry": "framboise",
    "raspberries": "framboises",
    
    # Viandes
    "chicken": "poulet",
    "beef": "bœuf",
    "pork": "porc",
    "lamb": "agneau",
    "fish": "poisson",
    "salmon": "saumon",
    "tuna": "thon",
    "shrimp": "crevette",
    "shrimps": "crevettes",
    "bacon": "lard",
    "ham": "jambon",
    "sausage": "saucisse",
    
    # Produits laitiers
    "milk": "lait",
    "cream": "crème",
    "butter": "beurre",
    "cheese": "fromage",
    "yogurt": "yaourt",
    "egg": "œuf",
    "eggs": "œufs",
    
    # Féculents
    "rice": "riz",
    "pasta": "pâtes",
    "bread": "pain",
    "flour": "farine",
    "sugar": "sucre",
    "salt": "sel",
    "pepper": "poivre",
    
    # Herbes et épices
    "basil": "basilic",
    "oregano": "origan",
    "thyme": "thym",
    "rosemary": "romarin",
    "parsley": "persil",
    "cilantro": "coriandre",
    "cinnamon": "cannelle",
    "nutmeg": "muscade",
    "vanilla": "vanille",
    "ginger": "gingembre",
    "garlic powder": "ail en poudre",
    "onion powder": "oignon en poudre",
    
    # Huiles et graisses
    "oil": "huile",
    "olive oil": "huile d'olive",
    "vegetable oil": "huile végétale",
    "butter": "beurre",
    
    # Autres
    "water": "eau",
    "vinegar": "vinaigre",
    "soy sauce": "sauce soja",
    "tomato sauce": "sauce tomate",
    "ketchup": "ketchup",
    "mustard": "moutarde",
    "mayonnaise": "mayonnaise",
    "honey": "miel",
    "chocolate": "chocolat",
    "coffee": "café",
    "tea": "thé",
}

# Mapping des unités étrangères vers le français
UNIT_MAPPINGS = {
    # Volume
    "cup": "tasse",
    "cups": "tasses",
    "tablespoon": "cuillère à soupe",
    "tablespoons": "cuillères à soupe",
    "tbsp": "cuillère à soupe",
    "teaspoon": "cuillère à café",
    "teaspoons": "cuillères à café",
    "tsp": "cuillère à café",
    "fluid ounce": "once liquide",
    "fl oz": "once liquide",
    "pint": "pinte",
    "quart": "quart",
    "gallon": "gallon",
    "liter": "litre",
    "liters": "litres",
    "ml": "ml",
    "milliliter": "millilitre",
    "milliliters": "millilitres",
    "l": "l",
    
    # Poids
    "ounce": "once",
    "ounces": "onces",
    "oz": "once",
    "pound": "livre",
    "pounds": "livres",
    "lb": "livre",
    "lbs": "livres",
    "gram": "gramme",
    "grams": "grammes",
    "g": "g",
    "kg": "kg",
    "kilogram": "kilogramme",
    "kilograms": "kilogrammes",
    "milligram": "milligramme",
    "milligrams": "milligrammes",
    "mg": "mg",
    
    # Unités spécifiques
    "piece": "pièce",
    "pieces": "pièces",
    "slice": "tranche",
    "slices": "tranches",
    "clove": "gousse",
    "cloves": "gousses",
    "head": "tête",
    "bunch": "botte",
    "bunches": "botte",
    "stalk": "tige",
    "stalks": "tiges",
    "leaf": "feuille",
    "leaves": "feuilles",
    "pinch": "pincée",
    "dash": "soupçon",
    "can": "boîte",
    "cans": "boîtes",
    "jar": "bocal",
    "jars": "bocaux",
    "package": "paquet",
    "packages": "paquets",
    "packet": "paquet",
    "packets": "paquets",
    "box": "boîte",
    "boxes": "boîtes",
    "bag": "sac",
    "bags": "sacs",
    
    # Déjà en français ou universels
    "tasse": "tasse",
    "cuillère à soupe": "cuillère à soupe",
    "cuillère à café": "cuillère à café",
    "litre": "litre",
    "ml": "ml",
    "gramme": "gramme",
    "g": "g",
    "kg": "kg",
    "pièce": "pièce",
    "tranche": "tranche",
    "gousse": "gousse",
}


class IngredientNormalizer:
    """Normalise les ingrédients pour l'import Mealie"""
    
    def __init__(self):
        self.translation_dict = INGREDIENT_TRANSLATIONS
        self.unit_mappings = UNIT_MAPPINGS
    
    def normalize_ingredient_name(self, name: str) -> str:
        """
        Normalise le nom d'un ingrédient
        
        Args:
            name: Nom de l'ingrédient
            
        Returns:
            Nom normalisé (lowercase, sans accents, trim)
        """
        if not name:
            return ""
        
        # Convertir en lowercase
        normalized = name.lower().strip()
        
        # Supprimer les accents
        normalized = unicodedata.normalize('NFKD', normalized)
        normalized = ''.join([c for c in normalized if not unicodedata.combining(c)])
        
        # Supprimer les caractères spéciaux et les chiffres
        normalized = re.sub(r'[^a-z\s-]', '', normalized)
        
        # Supprimer les espaces multiples
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def translate_to_french(self, name: str) -> str:
        """
        Traduit le nom d'un ingrédient en français
        
        Args:
            name: Nom de l'ingrédient (normalisé)
            
        Returns:
            Nom traduit en français
        """
        if not name:
            return ""
        
        # Normaliser d'abord
        normalized = self.normalize_ingredient_name(name)
        
        # Chercher dans le dictionnaire
        if normalized in self.translation_dict:
            return self.translation_dict[normalized]
        
        # Si pas trouvé, retourner le nom original (déjà peut-être en français)
        return name
    
    def standardize_unit(self, unit: str) -> str:
        """
        Standardise une unité de mesure
        
        Args:
            unit: Unité à standardiser
            
        Returns:
            Unité standardisée en français
        """
        if not unit:
            return ""
        
        # Normaliser
        normalized = unit.lower().strip()
        
        # Chercher dans le mapping
        if normalized in self.unit_mappings:
            return self.unit_mappings[normalized]
        
        # Si pas trouvé, retourner l'unité originale
        return unit
    
    def normalize_ingredient(self, name: str, unit: Optional[str] = None) -> Dict[str, str]:
        """
        Normalise complètement un ingrédient (nom + unité)
        
        Args:
            name: Nom de l'ingrédient
            unit: Unité optionnelle
            
        Returns:
            Dict avec 'name' et 'unit' normalisés
        """
        result = {
            'name': self.translate_to_french(name),
            'unit': self.standardize_unit(unit) if unit else ""
        }
        
        return result


# Fonctions utilitaires pour un usage rapide
def normalize_name(name: str) -> str:
    """Normalise un nom d'ingrédient"""
    normalizer = IngredientNormalizer()
    return normalizer.normalize_ingredient_name(name)


def translate_name(name: str) -> str:
    """Traduit un nom en français"""
    normalizer = IngredientNormalizer()
    return normalizer.translate_to_french(name)


def standardize_unit(unit: str) -> str:
    """Standardise une unité"""
    normalizer = IngredientNormalizer()
    return normalizer.standardize_unit(unit)


if __name__ == "__main__":
    # Tests
    normalizer = IngredientNormalizer()
    
    print("=== Tests de normalisation ===")
    test_names = ["Tomato", "Garlic cloves", "Chicken breast", "Olive oil"]
    for name in test_names:
        normalized = normalizer.normalize_ingredient_name(name)
        translated = normalizer.translate_to_french(name)
        print(f"{name} -> {normalized} -> {translated}")
    
    print("\n=== Tests de standardisation d'unités ===")
    test_units = ["cup", "tbsp", "oz", "g", "tasse"]
    for unit in test_units:
        standardized = normalizer.standardize_unit(unit)
        print(f"{unit} -> {standardized}")
