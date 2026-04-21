#!/usr/bin/env python3
"""
Parser intelligent hybride pour ingrédients
Combine règles rapides (80% cas) et IA (20% cas complexes)
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ModifierType(Enum):
    """Type de modifier"""
    PREPARATION = "preparation"  # coupé en dés, émincé, etc.
    VARIETY = "variety"          # au basilic, non épluchées, etc.
    QUANTITY = "quantity"        # filets, morceaux, etc.
    BRAND = "brand"             # herta®, le bon paris®, etc.
    UNKNOWN = "unknown"


@dataclass
class ParsedIngredient:
    """Résultat du parsing d'un ingrédient"""
    original: str
    base: str                    # Ingrédient principal (ex: "poulet")
    modifiers: List[Dict]        # List of {type, value}
    confidence: float            # 0-1, confiance du parsing
    method: str                  # "rules" ou "ai"


class IngredientParser:
    """Parser hybride d'ingrédients"""
    
    def __init__(self, use_ai: bool = True, ai_client=None):
        """
        Initialise le parser
        
        Args:
            use_ai: Utiliser l'IA pour les cas complexes
            ai_client: Client IA (Mistral)
        """
        self.use_ai = use_ai
        self.ai_client = ai_client
        
        # Patterns de préparation
        self.preparation_patterns = [
            r'(?:très|finement|grossièrement)?\s*(?:coupés?|émincés?|hachés?|découpés?|taillés?|tranchés?)\s*(?:en|dans|à)\s*(?:dés|cubes|morceaux|tranches|lamelles|rondelles|brunoise)',
            r'(?:pré)?(?:cuits?|sautés?|poêlés?|grillés?|rôtis?|bouillis?|vapeur)',
            r'(?:décortiqués?|épluchés?|vidés?|épinés?|désossés?|non épluchés?|non épluchée)',
            r'(?:lavés?|rincés?|égouttés?|séchés?)',
            r'(?:marinés?|assaisonnés?|aromatisés?)',
            r'(?:à l\'étouffée|à l\'étouffé)',
        ]
        
        # Patterns de quantité/coupe
        self.quantity_patterns = [
            r'(?:filets|morceaux|bouts|morceau|bout|pièces|dés|cubes|rondelles|tranches|lamelles|brins|feuilles|gousses|têtes|bottes)',
            r'(?:entier|entière|entiers|entières)',
        ]
        
        # Patterns de marque
        self.brand_patterns = [
            r'[a-z]+®',
            r'(?:herta|bon paris|richesmonts|trésor de grand-mère|knorr|maggi|liebig)',
        ]
        
        # Patterns de variété
        self.variety_patterns = [
            r'(?:au|à la|aux)\s+(?:basilic|romarin|thym|origan|persil|coriandre|menthe|cannelle|vanille|citron|orange|fraise|fraise des bois|noisette|noix|pistache|amande|chocolat|caramel|miel|érable|truffe|safran|curry|curcuma|gingembre|ail|oignon|échalote|poivre|piment|chili|curry|lait|soja|tomate|olive|noix|sésame|pistache|amande|noisette)',
            r'(?:de|du|des)\s+(?:forêt|mer|montagne|bretagne|normandie|provence|italie|espagne|inde|chine|japon|mexique|thailande)',
            r'(?:bio|organique|nature|entier|entière|entiers|entières|sauvage|domestique|fermier|fermière|artisanal|artisanale|maison|fait maison)',
        ]
        
        # Mots à ignorer (connecteurs)
        self.ignore_words = [
            r'(?:de|du|des|la|le|les|un|une|dans|en|à|au|aux|avec|sans|pour|et|ou|ou bien)',
        ]
    
    def parse(self, ingredient: str) -> ParsedIngredient:
        """
        Parse un ingrédient en base + modifiers
        
        Args:
            ingredient: Nom de l'ingrédient
            
        Returns:
            ParsedIngredient
        """
        # Essayer les règles d'abord (rapide)
        result = self._parse_with_rules(ingredient)
        
        # Si confiance faible et IA disponible, utiliser l'IA
        if result.confidence < 0.55 and self.use_ai and self.ai_client:
            result = self._parse_with_ai(ingredient)
        
        return result
    
    def _parse_with_rules(self, ingredient: str) -> ParsedIngredient:
        """
        Parse avec des règles regex (rapide)
        
        Args:
            ingredient: Nom de l'ingrédient
            
        Returns:
            ParsedIngredient
        """
        ingredient_lower = ingredient.lower()
        modifiers = []
        base = ingredient_lower
        confidence = 0.5
        
        # Extraire les marque
        for pattern in self.brand_patterns:
            matches = re.findall(pattern, ingredient_lower, re.IGNORECASE)
            for match in matches:
                modifiers.append({
                    'type': ModifierType.BRAND.value,
                    'value': match
                })
                # Retirer du base
                base = base.replace(match, '').strip()
        
        # Extraire la préparation
        for pattern in self.preparation_patterns:
            matches = re.findall(pattern, ingredient_lower, re.IGNORECASE)
            for match in matches:
                modifiers.append({
                    'type': ModifierType.PREPARATION.value,
                    'value': match
                })
                # Retirer du base
                base = base.replace(match, '').strip()
        
        # Extraire la quantité/coupe
        for pattern in self.quantity_patterns:
            matches = re.findall(pattern, ingredient_lower, re.IGNORECASE)
            for match in matches:
                modifiers.append({
                    'type': ModifierType.QUANTITY.value,
                    'value': match
                })
                # Retirer du base
                base = base.replace(match, '').strip()
        
        # Extraire les variétés
        for pattern in self.variety_patterns:
            matches = re.findall(pattern, ingredient_lower, re.IGNORECASE)
            for match in matches:
                modifiers.append({
                    'type': ModifierType.VARIETY.value,
                    'value': match
                })
                # Retirer du base
                base = base.replace(match, '').strip()
        
        # Nettoyer le base (retirer parenthèses, connecteurs)
        base = re.sub(r'\([^)]*\)', '', base)  # Parenthèses
        base = re.sub(r'[(),]', '', base)  # Ponctuation
        
        # Retirer les connecteurs et mots vides au début/fin
        base = re.sub(r'^(?:de|du|des|la|le|les|un|une|dans|en|à|au|aux|avec|sans|pour|et|ou)\s+', '', base)
        base = re.sub(r'\s+(?:de|du|des|la|le|les|un|une|dans|en|à|au|aux|avec|sans|pour|et|ou)$', '', base)
        
        base = re.sub(r'\s+', ' ', base).strip()  # Espaces multiples
        
        # Si on a trouvé des modifiers, confiance élevée
        if modifiers:
            confidence = 0.8
        else:
            # Si pas de modifiers, confiance faible (peut-être besoin d'IA)
            confidence = 0.5
        
        return ParsedIngredient(
            original=ingredient,
            base=base,
            modifiers=modifiers,
            confidence=confidence,
            method="rules"
        )
    
    def _parse_with_ai(self, ingredient: str) -> ParsedIngredient:
        """
        Parse avec l'IA (lent mais précis)
        
        Args:
            ingredient: Nom de l'ingrédient
            
        Returns:
            ParsedIngredient
        """
        if not self.ai_client:
            # Fallback vers règles
            return self._parse_with_rules(ingredient)
        
        prompt = f"""Analyse cet ingrédient et extrais:
- base: l'ingrédient principal (ex: "poulet" pour "filets de poulet coupés en dés")
- modifiers: liste des modifications avec leur type (preparation, variety, quantity, brand)

Ingrédient: "{ingredient}"

Réponds en JSON uniquement:
{{
    "base": "...",
    "modifiers": [
        {{"type": "...", "value": "..."}}
    ]
}}"""
        
        try:
            response = self.ai_client.generate(prompt)
            
            # Extraire le JSON de la réponse (peut être dans du texte)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
            else:
                # Si pas de JSON trouvé, essayer de parser toute la réponse
                result = json.loads(response)
            
            # Structurer les modifiers
            modifiers = []
            for mod in result.get('modifiers', []):
                modifiers.append({
                    'type': mod.get('type', ModifierType.UNKNOWN.value),
                    'value': mod.get('value', '')
                })
            
            return ParsedIngredient(
                original=ingredient,
                base=result.get('base', ingredient),
                modifiers=modifiers,
                confidence=0.9,
                method="ai"
            )
        except Exception as e:
            # Log l'erreur pour débogage
            print(f"⚠️ Erreur IA pour '{ingredient}': {e}")
            # Fallback vers règles mais indiquer qu'on a essayé l'IA
            rule_result = self._parse_with_rules(ingredient)
            return ParsedIngredient(
                original=ingredient,
                base=rule_result.base,
                modifiers=rule_result.modifiers,
                confidence=rule_result.confidence * 0.9,  # Réduire confiance car IA a échoué
                method="ai_fallback"
            )
    
    def should_merge(self, parsed_new: ParsedIngredient, parsed_existing: ParsedIngredient) -> bool:
        """
        Décide si deux ingrédients doivent être regroupés
        
        Args:
            parsed_new: Nouvel ingrédient parsé
            parsed_existing: Ingrédient existant parsé
            
        Returns:
            True si regroupement recommandé
        """
        # Si bases différentes, pas de regroupement
        if parsed_new.base.lower() != parsed_existing.base.lower():
            return False
        
        # Si bases identiques, comparer les modifiers
        new_mods_set = set((m['type'], m['value']) for m in parsed_new.modifiers)
        existing_mods_set = set((m['type'], m['value']) for m in parsed_existing.modifiers)
        
        # Si même modifiers → regrouper
        if new_mods_set == existing_mods_set:
            return True
        
        # Si aucun des deux n'a de modifiers → regrouper
        if not new_mods_set and not existing_mods_set:
            return True
        
        # Si l'un a des modifiers et l'autre non → créer nouveau
        if (not new_mods_set and existing_mods_set) or (new_mods_set and not existing_mods_set):
            return False
        
        # Si les deux ont des modifiers mais différents → créer nouveau
        # (surtout s'il y a des variétés ou marques)
        new_has_important_mods = any(m['type'] in [ModifierType.VARIETY.value, ModifierType.BRAND.value] for m in parsed_new.modifiers)
        existing_has_important_mods = any(m['type'] in [ModifierType.VARIETY.value, ModifierType.BRAND.value] for m in parsed_existing.modifiers)
        
        if new_has_important_mods or existing_has_important_mods:
            return False
        
        # Si seulement des préparations/quantités différentes → peut-être créer nouveau (prudent)
        return False


# Fonction utilitaire pour usage rapide
def parse_ingredient(ingredient: str, use_ai: bool = False, ai_client=None) -> ParsedIngredient:
    """Parse un ingrédient"""
    parser = IngredientParser(use_ai=use_ai, ai_client=ai_client)
    return parser.parse(ingredient)


if __name__ == "__main__":
    # Tests
    parser = IngredientParser(use_ai=False)
    
    test_ingredients = [
        "filets de poulet coupés en dés",
        "poulet",
        "ail (toutes les gousses non épluchées)",
        "ail",
        "huile d'olive (je la prends au basilic)",
        "huile d'olive",
        "oignons très finement émincé",
        "oignon",
    ]
    
    print("=== Tests de parsing ===")
    for ingredient in test_ingredients:
        parsed = parser.parse(ingredient)
        print(f"\n{ingredient}")
        print(f"  Base: {parsed.base}")
        print(f"  Modifiers: {parsed.modifiers}")
        print(f"  Confiance: {parsed.confidence}")
        print(f"  Méthode: {parsed.method}")
