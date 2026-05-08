"""
Mapper entre les ingrédients Mealie et les produits Carrefour.
Permet de trouver les meilleurs produits Carrefour correspondant à une liste de courses Mealie.
"""

from typing import List, Dict, Optional, Tuple
import re
import asyncio

from scrapers.carrefour_scraper import CarrefourScraper


class MealieToCarrefourMapper:
    """
    Mapper pour associer les ingrédients Mealie aux produits Carrefour.
    
    Fonctionnalités:
    - Nettoyage et normalisation des noms d'ingrédients
    - Recherche de synonymes
    - Filtrage par unité compatible
    - Sélection du meilleur produit (prix, disponibilité)
    """
    
    # Base de données de synonymes (à étendre)
    SYNONYMS = {
        # Produits de base
        "oeuf": ["œuf", "oeufs", "œufs"],
        "farine": ["farine", "farine de blé", "farine t55", "farine t45", "farine de froment"],
        "lait": ["lait", "lait entier", "lait demi-écrémé", "lait écrémé", "lait de vache"],
        "beurre": ["beurre", "beurre doux", "beurre demi-sel", "beurre salé"],
        "sucre": ["sucre", "sucre en poudre", "sucre blanc", "sucre de canne"],
        "sel": ["sel", "sel fin", "sel de table", "sel marin"],
        
        # Viandes
        "poulet": ["poulet", "poulet entier", "volaille"],
        "boeuf": ["boeuf", "bœuf", "viande de boeuf"],
        "porc": ["porc", "viande de porc"],
        
        # Légumes
        "tomate": ["tomate", "tomates"],
        "oignon": ["oignon", "oignons"],
        "ail": ["ail", "gousse d'ail", "tête d'ail"],
        "carotte": ["carotte", "carottes"],
        "pomme de terre": ["pomme de terre", "pommes de terre", "patate"],
        
        # Fruits
        "pomme": ["pomme", "pommes"],
        "banane": ["banane", "bananes"],
        "orange": ["orange", "oranges"],
        
        # Produits laitiers
        "fromage": ["fromage", "fromages"],
        "yaourt": ["yaourt", "yaourts", "yaourt nature"],
        "crème": ["crème", "crème fraîche", "crème liquide"],
        
        # Épicerie
        "pâte": ["pâte", "pâtes", "pâtes alimentaires"],
        "riz": ["riz", "riz blanc", "riz basmati"],
        "huile": ["huile", "huile d'olive", "huile de tournesol"],
        "vinaigre": ["vinaigre", "vinaigre de vin", "vinaigre balsamique"],
        
        # Boissons
        "eau": ["eau", "eau plate", "eau gazeuse"],
        "café": ["café", "café moulu", "café en grain"],
        "thé": ["thé", "thé vert", "thé noir"],
    }
    
    # Correspondance des unités Mealie → Unités Carrefour
    UNIT_CONVERSION = {
        "g": ["g", "gramme", "grammes"],
        "kg": ["kg", "kilogramme", "kilogrammes", "kilo"],
        "mg": ["mg", "milligramme", "milligrammes"],
        "L": ["L", "l", "litre", "litres"],
        "mL": ["mL", "ml", "millilitre", "millilitres"],
        "cL": ["cL", "cl", "centilitre", "centilitres"],
        "pièce": ["pièce", "pièces", "unité", "unités", "u"],
        "boîte": ["boîte", "boîtes"],
        "sachet": ["sachet", "sachets"],
        "barquette": ["barquette", "barquettes"],
        "bouteille": ["bouteille", "bouteilles"],
        "canette": ["canette", "canettes"],
        "pot": ["pot", "pots"],
        "tablette": ["tablette", "tablettes"],
    }
    
    # Unités par défaut pour les produits sans unité claire
    DEFAULT_UNITS = {
        "oeuf": "pièce",
        "pomme de terre": "kg",
        "oignon": "kg",
        "ail": "pièce",
        "tomate": "kg",
        "carotte": "kg",
        "pomme": "pièce",
        "banane": "kg",
        "orange": "pièce",
        "lait": "L",
        "farine": "kg",
        "sucre": "kg",
        "sel": "g",
        "huile": "L",
        "vinaigre": "L",
        "eau": "L",
        "pâte": "g",
        "riz": "g",
    }
    
    def __init__(self):
        """Initialise le mapper avec un scraper Carrefour."""
        self.scraper = CarrefourScraper()
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalise un texte pour la comparaison.
        - Passe en minuscules
        - Supprime les accents
        - Supprime les caractères spéciaux
        - Supprime les termes génériques
        """
        if not text:
            return ""
        
        # Minuscules
        text = text.lower()
        
        # Suppression des accents
        text = text.replace("œ", "oe").replace("æ", "ae")
        text = text.replace("à", "a").replace("â", "a").replace("ä", "a")
        text = text.replace("ç", "c")
        text = text.replace("é", "e").replace("è", "e").replace("ê", "e").replace("ë", "e")
        text = text.replace("î", "i").replace("ï", "i")
        text = text.replace("ô", "o").replace("ö", "o")
        text = text.replace("ù", "u").replace("û", "u").replace("ü", "u")
        text = text.replace("ÿ", "y")
        
        # Suppression des caractères spéciaux (sauf espaces et tirets)
        text = re.sub(r"[^\w\s-]", "", text)
        
        # Suppression des termes génériques
        generic_terms = [
            "bio", "ab", "label rouge", "igp", "aop", 
            "carrefour", "marque distributeur", "md", 
            "en promo", "promotion", "soldes", "réduction",
            "offre", "spécial", "exclusif", "nouveau",
            "le", "la", "les", "du", "de", "des",
        ]
        for term in generic_terms:
            text = text.replace(term, "").strip()
        
        # Suppression des espaces multiples
        text = re.sub(r"\s+", " ", text).strip()
        
        return text
    
    def _get_synonyms(self, ingredient: str) -> List[str]:
        """
        Récupère les synonymes pour un ingrédient.
        
        Args:
            ingredient: Nom de l'ingrédient
            
        Returns:
            Liste des synonymes (incluant l'ingrédient normalisé)
        """
        normalized = self._normalize_text(ingredient)
        
        # Recherche dans la base de synonymes
        for key, synonyms in self.SYNONYMS.items():
            if normalized in [self._normalize_text(s) for s in synonyms]:
                return synonyms + [normalized]
        
        # Retourne l'ingrédient normalisé seul
        return [normalized, ingredient.lower()]
    
    def _are_units_compatible(self, product_unit: Optional[str], ingredient_unit: str) -> bool:
        """
        Vérifie si les unités sont compatibles.
        
        Args:
            product_unit: Unité du produit Carrefour
            ingredient_unit: Unité de l'ingrédient Mealie
            
        Returns:
            True si les unités sont compatibles
        """
        if not product_unit or not ingredient_unit:
            return False
        
        product_unit_normalized = self._normalize_text(product_unit)
        ingredient_unit_normalized = self._normalize_text(ingredient_unit)
        
        # Vérification directe
        if product_unit_normalized == ingredient_unit_normalized:
            return True
        
        # Vérification via la table de conversion
        if ingredient_unit_normalized in self.UNIT_CONVERSION:
            compatible_units = [
                self._normalize_text(u) 
                for u in self.UNIT_CONVERSION[ingredient_unit_normalized]
            ]
            return product_unit_normalized in compatible_units
        
        return False
    
    def _get_default_unit(self, ingredient: str) -> str:
        """
        Récupère l'unité par défaut pour un ingrédient.
        
        Args:
            ingredient: Nom de l'ingrédient
            
        Returns:
            Unité par défaut
        """
        normalized = self._normalize_text(ingredient)
        
        for key, unit in self.DEFAULT_UNITS.items():
            if normalized == self._normalize_text(key):
                return unit
        
        # Unité par défaut : pièce
        return "pièce"
    
    async def _search_products(
        self, 
        ingredient: str, 
        quantity: float, 
        unit: str
    ) -> List[Dict]:
        """
        Recherche les produits Carrefour correspondants à un ingrédient.
        
        Args:
            ingredient: Nom de l'ingrédient
            quantity: Quantité nécessaire
            unit: Unité de la quantité
            
        Returns:
            Liste des produits Carrefour pertinents
        """
        # Normalisation et synonymes
        synonyms = self._get_synonyms(ingredient)
        
        # Construction des requêtes de recherche
        queries = []
        for synonym in synonyms:
            # Requête simple
            queries.append(synonym)
            # Requête avec unité
            queries.append(f"{synonym} {unit}")
        
        # Recherche sur Carrefour
        all_products = []
        for query in queries:
            try:
                products = await self.scraper.search_products(query)
                all_products.extend(products)
            except Exception as e:
                print(f"Erreur lors de la recherche pour '{query}': {e}")
                continue
        
        # Suppression des doublons (même URL)
        unique_products = {}
        for product in all_products:
            if product["url"] not in unique_products:
                unique_products[product["url"]] = product
        
        return list(unique_products.values())
    
    def _filter_compatible_products(
        self, 
        products: List[Dict], 
        ingredient_unit: str
    ) -> List[Dict]:
        """
        Filtre les produits compatibles avec l'unité de l'ingrédient.
        
        Args:
            products: Liste des produits à filtrer
            ingredient_unit: Unité de l'ingrédient Mealie
            
        Returns:
            Liste des produits compatibles
        """
        compatible_products = []
        
        for product in products:
            # Vérification de la compatibilité des unités
            product_unit = product.get("unit")
            if self._are_units_compatible(product_unit, ingredient_unit):
                compatible_products.append(product)
            # Si pas d'unité produit, on assume compatible
            elif product_unit is None:
                compatible_products.append(product)
        
        return compatible_products
    
    def _calculate_required_quantity(
        self, 
        product: Dict, 
        needed_quantity: float, 
        needed_unit: str
    ) -> Tuple[float, str]:
        """
        Calcule la quantité nécessaire d'un produit pour répondre au besoin.
        
        Args:
            product: Produit Carrefour
            needed_quantity: Quantité nécessaire
            needed_unit: Unité de la quantité nécessaire
            
        Returns:
            Tuple (quantité à acheter, unité)
        """
        # Si le produit n'a pas d'unité ou de poids, on retourne la quantité nécessaire
        if product.get("unit") is None and product.get("weight") is None:
            return needed_quantity, needed_unit
        
        # Si le produit a un poids (en kg)
        if product.get("weight") is not None:
            product_weight_kg = product["weight"]
            
            # Conversion de la quantité nécessaire en kg
            needed_quantity_kg = needed_quantity
            if needed_unit == "g":
                needed_quantity_kg = needed_quantity / 1000
            elif needed_unit == "mg":
                needed_quantity_kg = needed_quantity / 1000000
            
            # Calcul de la quantité à acheter (en unités du produit)
            if product.get("unit") == "kg":
                return needed_quantity_kg, "kg"
            elif product.get("unit") == "g":
                return needed_quantity_kg * 1000, "g"
            else:
                return needed_quantity, needed_unit
        
        # Si le produit a un conditionnement (quantité par pack)
        if product.get("quantity_in_pack") is not None:
            pack_quantity = product["quantity_in_pack"]
            pack_unit = product.get("unit", "pièce")
            
            if pack_unit == needed_unit:
                # Calcul du nombre de packs nécessaires
                packs_needed = needed_quantity / pack_quantity
                return packs_needed, "pack"
        
        # Cas par défaut
        return needed_quantity, needed_unit
    
    async def map_ingredient(
        self, 
        ingredient: str, 
        quantity: float, 
        unit: str
    ) -> Dict:
        """
        Trouve le meilleur produit Carrefour pour un ingrédient Mealie.
        
        Args:
            ingredient: Nom de l'ingrédient
            quantity: Quantité nécessaire
            unit: Unité de la quantité
            
        Returns:
            Dictionnaire avec les informations du meilleur produit
        """
        # Recherche des produits
        products = await self._search_products(ingredient, quantity, unit)
        
        if not products:
            return {
                "ingredient": ingredient,
                "quantity": quantity,
                "unit": unit,
                "error": "Aucun produit trouvé",
                "suggestions": self._get_synonyms(ingredient)
            }
        
        # Filtrage des produits compatibles
        compatible_products = self._filter_compatible_products(products, unit)
        
        if not compatible_products:
            # Si aucun produit compatible, on prend tous les produits
            compatible_products = products
        
        # Tri des produits (par prix/unité, puis par disponibilité)
        sorted_products = sorted(
            compatible_products,
            key=lambda p: (
                p.get("price_per_unit") or float('inf'),
                not p.get("availability", True),
                p.get("price") or float('inf')
            )
        )
        
        best_product = sorted_products[0]
        
        # Calcul de la quantité à acheter
        required_quantity, required_unit = self._calculate_required_quantity(
            best_product, quantity, unit
        )
        
        return {
            "ingredient": ingredient,
            "quantity_needed": quantity,
            "unit_needed": unit,
            "product_name": best_product.get("name"),
            "product_brand": best_product.get("brand"),
            "product_price": best_product.get("price"),
            "product_price_per_unit": best_product.get("price_per_unit"),
            "product_weight": best_product.get("weight"),
            "product_unit": best_product.get("unit"),
            "product_packaging": best_product.get("packaging"),
            "product_url": best_product.get("url"),
            "product_availability": best_product.get("availability"),
            "quantity_to_buy": required_quantity,
            "unit_to_buy": required_unit,
            "total_cost": best_product.get("price") * (required_quantity if best_product.get("unit") == required_unit else 1),
            "why": self._get_selection_reason(best_product, sorted_products)
        }
    
    def _get_selection_reason(self, product: Dict, all_products: List[Dict]) -> str:
        """
        Génère une explication pour le choix du produit.
        
        Args:
            product: Produit sélectionné
            all_products: Liste de tous les produits trouvés
            
        Returns:
            Chaîne expliquant le choix
        """
        reasons = []
        
        if len(all_products) == 1:
            reasons.append("Seul produit trouvé")
        else:
            # Comparaison avec le deuxième meilleur
            if len(all_products) > 1:
                second_product = all_products[1]
                if product.get("price_per_unit") < second_product.get("price_per_unit"):
                    price_diff = second_product.get("price_per_unit", 0) - product.get("price_per_unit", 0)
                    reasons.append(f"Meilleur prix/unité (économie: {price_diff:.2f}€)")
            
            if product.get("availability"):
                reasons.append("Disponible en stock")
        
        return ", ".join(reasons)
    
    async def map_shopping_list(self, shopping_list: List[Dict]) -> List[Dict]:
        """
        Mappe une liste de courses Mealie complète vers des produits Carrefour.
        
        Args:
            shopping_list: Liste d'ingrédients au format Mealie
                          [{"name": "Œufs", "quantity": 6, "unit": "pièce"}, ...]
            
        Returns:
            Liste de produits optimisés
        """
        results = []
        
        for item in shopping_list:
            try:
                result = await self.map_ingredient(
                    ingredient=item.get("name", ""),
                    quantity=item.get("quantity", 1),
                    unit=item.get("unit", self._get_default_unit(item.get("name", "")))
                )
                results.append(result)
            except Exception as e:
                results.append({
                    "ingredient": item.get("name", ""),
                    "error": str(e)
                })
        
        return results
    
    async def close(self):
        """Fermeture propre du scraper."""
        await self.scraper.close()
    
    async def __aenter__(self):
        """Pour utilisation avec async with."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Fermeture automatique."""
        await self.close()


# Exemple d'utilisation
if __name__ == "__main__":
    import asyncio
    
    async def test_mapper():
        async with MealieToCarrefourMapper() as mapper:
            # Test avec un seul ingrédient
            result = await mapper.map_ingredient("Œufs", 6, "pièce")
            print("Meilleur produit pour 6 œufs:")
            print(f"  {result.get('product_name')} - {result.get('product_price')}€")
            print(f"  URL: {result.get('product_url')}")
            print()
            
            # Test avec une liste de courses
            shopping_list = [
                {"name": "Œufs", "quantity": 6, "unit": "pièce"},
                {"name": "Farine T55", "quantity": 500, "unit": "g"},
                {"name": "Lait entier", "quantity": 1, "unit": "L"}
            ]
            results = await mapper.map_shopping_list(shopping_list)
            print("Liste de courses optimisée:")
            for r in results:
                if "error" not in r:
                    print(f"  {r['ingredient']} -> {r['product_name']} ({r['product_price']}€)")
    
    asyncio.run(test_mapper())
