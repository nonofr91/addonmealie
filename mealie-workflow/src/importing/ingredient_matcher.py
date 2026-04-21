#!/usr/bin/env python3
"""
Module de matching des ingrédients pour l'import Mealie
Fait du fuzzy matching avec les ingrédients existants dans Mealie
"""

import unicodedata
import re
from typing import Dict, List, Optional
from dataclasses import dataclass

try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    try:
        from fuzzywuzzy import fuzz, process
        RAPIDFUZZ_AVAILABLE = False
    except ImportError:
        # Fallback: implémentation basique de similarité
        RAPIDFUZZ_AVAILABLE = False
        fuzz = None
        process = None

try:
    from .ingredient_normalizer import IngredientNormalizer
except ImportError:
    try:
        from ingredient_normalizer import IngredientNormalizer
    except ImportError:
        # Si l'import échoue, définir une classe vide pour éviter l'erreur
        class IngredientNormalizer:
            def __init__(self):
                pass

try:
    from .ingredient_parser import IngredientParser
except ImportError:
    try:
        from ingredient_parser import IngredientParser
    except ImportError:
        # Si l'import échoue, définir une classe vide pour éviter l'erreur
        class IngredientParser:
            def __init__(self, use_ai=False, ai_client=None):
                pass
            def parse(self, ingredient):
                from dataclasses import dataclass
                @dataclass
                class ParsedIngredient:
                    original: str
                    base: str
                    modifiers: list
                    confidence: float
                    method: str
                return ParsedIngredient(original=ingredient, base=ingredient, modifiers=[], confidence=0.5, method="none")


@dataclass
class MatchResult:
    """Résultat du matching d'ingrédient"""
    matched: bool
    matched_item: Optional[Dict]
    similarity: float
    match_id: Optional[str] = None


class IngredientMatcher:
    """Matcher d'ingrédients avec fuzzy matching"""
    
    def __init__(self, similarity_threshold: float = 0.85, use_parser: bool = False, ai_client=None):
        """
        Initialise le matcher
        
        Args:
            similarity_threshold: Seuil de similarité (0-1)
            use_parser: Utiliser le parser hybride pour extraire base/modifiers
            ai_client: Client IA pour le parser (optionnel)
        """
        self.similarity_threshold = similarity_threshold
        self.normalizer = IngredientNormalizer()
        self.foods_cache: List[Dict] = []
        self.units_cache: List[Dict] = []
        self.use_parser = use_parser
        self.parser = IngredientParser(use_ai=use_parser, ai_client=ai_client) if use_parser else None
        
    def load_existing_foods(self, foods: List[Dict]) -> None:
        """
        Charge la liste des foods existants depuis Mealie
        
        Args:
            foods: Liste des foods depuis l'API Mealie
        """
        self.foods_cache = foods
        
    def load_existing_units(self, units: List[Dict]) -> None:
        """
        Charge la liste des units existants depuis Mealie
        
        Args:
            units: Liste des units depuis l'API Mealie
        """
        self.units_cache = units
    
    def calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calcule la similarité entre deux chaînes
        
        Args:
            str1: Première chaîne
            str2: Deuxième chaîne
            
        Returns:
            Score de similarité (0-100)
        """
        if not str1 or not str2:
            return 0.0
        
        if RAPIDFUZZ_AVAILABLE and fuzz is not None:
            # Utiliser rapidfuzz/fuzzywuzzy
            return fuzz.ratio(str1, str2)
        else:
            # Fallback: implémentation basique
            return self._basic_similarity(str1, str2)
    
    def _basic_similarity(self, str1: str, str2: str) -> float:
        """
        Implémentation basique de similarité (fallback)
        
        Args:
            str1: Première chaîne
            str2: Deuxième chaîne
            
        Returns:
            Score de similarité (0-100)
        """
        # Normaliser les chaînes
        norm1 = self._normalize_for_comparison(str1)
        norm2 = self._normalize_for_comparison(str2)
        
        if norm1 == norm2:
            return 100.0
        
        # Distance de Levenshtein simplifiée
        len1, len2 = len(norm1), len(norm2)
        
        if len1 == 0 or len2 == 0:
            return 0.0
        
        # Similarité basée sur les caractères communs
        common = 0
        for c in norm1:
            if c in norm2:
                common += 1
        
        # Similarité basée sur la longueur
        length_similarity = 1 - abs(len1 - len2) / max(len1, len2)
        
        # Moyenne pondérée
        similarity = (common / max(len1, len2)) * 0.7 + length_similarity * 0.3
        
        return similarity * 100
    
    def _normalize_for_comparison(self, text: str) -> str:
        """
        Normalise le texte pour la comparaison
        
        Args:
            text: Texte à normaliser
            
        Returns:
            Texte normalisé
        """
        if not text:
            return ""
        
        # Lowercase
        text = text.lower()
        
        # Supprimer les accents
        text = unicodedata.normalize('NFKD', text)
        text = ''.join([c for c in text if not unicodedata.combining(c)])
        
        # Supprimer les caractères spéciaux
        text = re.sub(r'[^a-z0-9]', '', text)
        
        return text
    
    def find_existing_food(self, name: str) -> MatchResult:
        """
        Cherche un food existant correspondant au nom donné
        
        Args:
            name: Nom de l'ingrédient à chercher
            
        Returns:
            MatchResult avec les détails du match
        """
        if not name or not self.foods_cache:
            return MatchResult(matched=False, matched_item=None, similarity=0.0)
        
        # Utiliser le parser si disponible pour extraire la base
        if self.use_parser and self.parser:
            parsed = self.parser.parse(name)
            # Utiliser la base extraite pour le matching
            names_to_match = [parsed.base, name.lower()]
        else:
            # Normaliser et traduire le nom
            normalized_name = self.normalizer.normalize_ingredient_name(name)
            translated_name = self.normalizer.translate_to_french(name)
            
            # Préparer les noms à comparer
            names_to_match = [normalized_name, translated_name, name.lower()]
        
        if RAPIDFUZZ_AVAILABLE and process is not None:
            # Utiliser rapidfuzz pour le matching
            food_names = [self._normalize_for_comparison(food.get('name', '')) for food in self.foods_cache]
            
            best_match = None
            best_score = 0
            best_food = None
            
            for name_to_match in names_to_match:
                normalized_match = self._normalize_for_comparison(name_to_match)
                result = process.extractOne(
                    normalized_match,
                    food_names,
                    scorer=fuzz.ratio
                )
                
                if result and result[1] > best_score:
                    best_score = result[1]
                    best_match = result[0]
            
            if best_score >= self.similarity_threshold * 100:
                # Trouver le food correspondant
                for food in self.foods_cache:
                    if self._normalize_for_comparison(food.get('name', '')) == best_match:
                        return MatchResult(
                            matched=True,
                            matched_item=food,
                            similarity=best_score / 100,
                            match_id=food.get('id')
                        )
        else:
            # Fallback: matching basique
            best_score = 0
            best_food = None
            
            for food in self.foods_cache:
                food_name = food.get('name', '')
                for name_to_match in names_to_match:
                    score = self.calculate_similarity(name_to_match, food_name)
                    if score > best_score:
                        best_score = score
                        best_food = food
            
            if best_score >= self.similarity_threshold * 100:
                return MatchResult(
                    matched=True,
                    matched_item=best_food,
                    similarity=best_score / 100,
                    match_id=best_food.get('id')
                )
        
        return MatchResult(matched=False, matched_item=None, similarity=0.0)
    
    def find_existing_unit(self, name: str) -> MatchResult:
        """
        Cherche une unité existante correspondant au nom donné
        
        Args:
            name: Nom de l'unité à chercher
            
        Returns:
            MatchResult avec les détails du match
        """
        if not name or not self.units_cache:
            return MatchResult(matched=False, matched_item=None, similarity=0.0)
        
        # Standardiser l'unité
        standardized_name = self.normalizer.standardize_unit(name)
        
        # Chercher une correspondance exacte d'abord
        for unit in self.units_cache:
            unit_name = unit.get('name', '').lower()
            if unit_name == standardized_name.lower():
                return MatchResult(
                    matched=True,
                    matched_item=unit,
                    similarity=1.0,
                    match_id=unit.get('id')
                )
        
        # Si pas de correspondance exacte, faire du fuzzy matching
        if RAPIDFUZZ_AVAILABLE and process is not None:
            unit_names = [unit.get('name', '') for unit in self.units_cache]
            result = process.extractOne(
                standardized_name,
                unit_names,
                scorer=fuzz.ratio
            )
            
            if result and result[1] >= self.similarity_threshold * 100:
                for unit in self.units_cache:
                    if unit.get('name') == result[0]:
                        return MatchResult(
                            matched=True,
                            matched_item=unit,
                            similarity=result[1] / 100,
                            match_id=unit.get('id')
                        )
        else:
            # Fallback: matching basique
            best_score = 0
            best_unit = None
            
            for unit in self.units_cache:
                unit_name = unit.get('name', '')
                score = self.calculate_similarity(standardized_name, unit_name)
                if score > best_score:
                    best_score = score
                    best_unit = unit
            
            if best_score >= self.similarity_threshold * 100:
                return MatchResult(
                    matched=True,
                    matched_item=best_unit,
                    similarity=best_score / 100,
                    match_id=best_unit.get('id')
                )
        
        return MatchResult(matched=False, matched_item=None, similarity=0.0)
    
    def match_ingredient(self, name: str, unit: Optional[str] = None) -> Dict[str, MatchResult]:
        """
        Match un ingrédient complet (food + unit)
        
        Args:
            name: Nom de l'ingrédient
            unit: Unité optionnelle
            
        Returns:
            Dict avec 'food' et 'unit' MatchResult
        """
        return {
            'food': self.find_existing_food(name),
            'unit': self.find_existing_unit(unit) if unit else MatchResult(matched=False, matched_item=None, similarity=0.0)
        }


# Fonctions utilitaires pour un usage rapide
def find_food_match(name: str, foods: List[Dict], threshold: float = 0.85) -> MatchResult:
    """Cherche un food existant"""
    matcher = IngredientMatcher(similarity_threshold=threshold)
    matcher.load_existing_foods(foods)
    return matcher.find_existing_food(name)


def find_unit_match(name: str, units: List[Dict], threshold: float = 0.85) -> MatchResult:
    """Cherche une unité existante"""
    matcher = IngredientMatcher(similarity_threshold=threshold)
    matcher.load_existing_units(units)
    return matcher.find_existing_unit(name)


if __name__ == "__main__":
    # Tests
    matcher = IngredientMatcher(similarity_threshold=0.85)
    
    print("=== Tests de similarité ===")
    print(f"Similarité 'poulet' vs 'poulet entier': {matcher.calculate_similarity('poulet', 'poulet entier')}")
    print(f"Similarité 'tomate' vs 'tomates': {matcher.calculate_similarity('tomate', 'tomates')}")
    print(f"Similarité 'tomato' vs 'tomate': {matcher.calculate_similarity('tomato', 'tomate')}")
    
    print("\n=== Tests de matching avec cache ===")
    test_foods = [
        {'id': '1', 'name': 'poulet'},
        {'id': '2', 'name': 'tomate'},
        {'id': '3', 'name': 'oignon'},
    ]
    matcher.load_existing_foods(test_foods)
    
    result = matcher.find_existing_food('poulet entier')
    print(f"Match 'poulet entier': {result.matched}, similarity={result.similarity}")
    
    result = matcher.find_existing_food('tomate')
    print(f"Match 'tomate': {result.matched}, similarity={result.similarity}")
