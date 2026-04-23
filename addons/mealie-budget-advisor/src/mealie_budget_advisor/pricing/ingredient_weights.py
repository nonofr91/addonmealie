"""Base de données de poids moyens par type d'ingrédient.

Utilisée pour convertir des quantités en "unit" (pièces) vers kg/l
pour le calcul des coûts.
"""

# Poids moyens en kg par unité/pièce
INGREDIENT_WEIGHTS = {
    # Légumes
    "courgette": 0.25,
    "courgettes": 0.25,
    "tomate": 0.12,
    "tomates": 0.12,
    "oignon": 0.15,
    "oignons": 0.15,
    "carotte": 0.075,
    "carottes": 0.075,
    "pomme de terre": 0.2,
    "pommes de terre": 0.2,
    "patate": 0.2,
    "patates": 0.2,
    "poivron": 0.15,
    "poivrons": 0.15,
    "aubergine": 0.3,
    "aubergines": 0.3,
    "épinard": 0.05,
    "épinards": 0.05,
    "salade": 0.2,
    "chou": 0.8,
    "choux": 0.8,
    "brocoli": 0.5,
    "concombre": 0.3,
    "ail": 0.005,  # 1 gousse
    "ails": 0.005,

    # Fruits
    "pomme": 0.15,
    "pommes": 0.15,
    "poire": 0.15,
    "poires": 0.15,
    "banane": 0.12,
    "bananes": 0.12,
    "orange": 0.15,
    "oranges": 0.15,
    "citron": 0.08,
    "citrons": 0.08,
    "pêche": 0.15,
    "pêches": 0.15,
    "abricot": 0.05,
    "abricots": 0.05,
    "fraise": 0.02,
    "fraises": 0.02,
    "raisin": 0.005,  # par grain
    "raisins": 0.005,

    # Viandes
    "cuisse de poulet": 0.2,
    "cuisses de poulet": 0.2,
    "poulet": 1.2,  # poulet entier
    "dinde": 2.0,
    "canard": 1.8,
    "côte de porc": 0.25,
    "côtes de porc": 0.25,
    "escalope de poulet": 0.15,
    "escalopes de poulet": 0.15,
    "steak": 0.2,
    "steaks": 0.2,
    "bœuf": 0.2,
    "veau": 0.2,
    "agneau": 0.2,
    "saucisse": 0.1,
    "saucisses": 0.1,
    "lardon": 0.01,
    "lardons": 0.01,

    # Poissons
    "filet de poisson": 0.15,
    "filets de poisson": 0.15,
    "saumon": 0.15,
    "thon": 0.15,
    "cabillaud": 0.15,
    "crevette": 0.02,
    "crevettes": 0.02,
    "moule": 0.01,
    "moules": 0.01,

    # Produits laitiers
    "œuf": 0.05,  # ~50g
    "œufs": 0.05,
    "oeuf": 0.05,
    "oeufs": 0.05,
    "fromage": 0.1,
    "fromages": 0.1,
    "tranche de fromage": 0.02,
    "tranches de fromage": 0.02,
    "beurre": 0.01,  # par noisette/cuillère
    "crème": 0.015,  # par cuillère à soupe

    # Féculents
    "pain": 0.05,  # par tranche
    "tranche de pain": 0.05,
    "tranches de pain": 0.05,
    "pâte": 0.1,  # par portion
    "pâtes": 0.1,

    # Herbes et épices (petites quantités)
    "basilic": 0.005,
    "persil": 0.005,
    "thym": 0.002,
    "laurier": 0.001,  # par feuille
    "feuille de laurier": 0.001,
    "feuilles de laurier": 0.001,
    "cumin": 0.001,
    "paprika": 0.001,
    "poivre": 0.001,
    "sel": 0.001,
    "épice": 0.002,
    "épices": 0.002,

    # Autres
    "citron vert": 0.08,
    "lime": 0.08,
    "gingembre": 0.02,
    "piment": 0.01,
}


def get_ingredient_weight(ingredient_name: str) -> float:
    """Retourne le poids moyen en kg pour un ingrédient.

    Args:
        ingredient_name: Nom de l'ingrédient

    Returns:
        Poids moyen en kg (0.15 par défaut)
    """
    name_lower = ingredient_name.lower().strip()
    
    # Recherche exacte
    if name_lower in INGREDIENT_WEIGHTS:
        return INGREDIENT_WEIGHTS[name_lower]
    
    # Recherche partielle (ex: "épices pour tajine" → "épices")
    for key, weight in INGREDIENT_WEIGHTS.items():
        if key in name_lower or name_lower in key:
            return weight
    
    # Poids par défaut
    return 0.15
