"""Filter recipes based on household allergies and dietary restrictions."""

from __future__ import annotations

import re

from ..models.profile import DietaryRestriction, HouseholdProfile, MemberProfile, MedicalCondition

RESTRICTION_KEYWORDS: dict[DietaryRestriction, list[str]] = {
    DietaryRestriction.vegetarian: [
        "viande", "poulet", "boeuf", "porc", "veau", "agneau", "lard", "bacon",
        "jambon", "saucisse", "steak", "canard", "dinde", "lapin", "gibier",
        "saumon", "thon", "cabillaud", "crevette", "moule", "coquille",
    ],
    DietaryRestriction.vegan: [
        "viande", "poulet", "boeuf", "porc", "veau", "agneau", "lard", "bacon",
        "jambon", "saucisse", "steak", "canard", "dinde", "lapin", "gibier",
        "saumon", "thon", "cabillaud", "crevette", "moule", "coquille",
        "lait", "beurre", "crème", "fromage", "yaourt", "œuf", "miel",
    ],
    DietaryRestriction.gluten_free: [
        "farine", "blé", "pain", "pâtes", "semoule", "orge", "seigle", "épeautre",
        "couscous", "boulghour",
    ],
    DietaryRestriction.lactose_free: [
        "lait", "beurre", "crème", "fromage", "yaourt",
    ],
}

MEDICAL_KEYWORDS: dict[MedicalCondition, list[str]] = {
    MedicalCondition.gout: [
        "viande rouge", "boeuf", "agneau", "veau", "porc",
        "foie", "rognons", "abats",
        "sardine", "anchois", "maquereau", "hareng",
        "crevette", "crabe", "homard", "langouste", "moule", "coquille",
        "bière", "alcool",
    ],
    MedicalCondition.gerd: [
        "piment", "chili", "poivre", "curry", "cayenne",
        "citron", "orange", "pamplemousse", "tomate", "vinaigre",
        "café", "thé", "chocolat", "alcool", "menthe",
        "ail", "oignon",
    ],
    MedicalCondition.kidney_disease: [
        "banane", "avocat", "épinard", "pomme de terre",
        "noix", "amande", "cacahuète",
    ],
}


def _ingredient_texts(recipe: dict) -> list[str]:
    """Extrait tous les textes d'ingrédients d'une recette Mealie."""
    texts: list[str] = []
    for ing in recipe.get("recipeIngredient", []):
        if isinstance(ing, str):
            texts.append(ing.lower())
        elif isinstance(ing, dict):
            texts.append((ing.get("note", "") or ing.get("display", "") or "").lower())
    texts.append((recipe.get("name", "") + " " + recipe.get("description", "")).lower())
    return texts


def _contains(texts: list[str], keywords: list[str]) -> list[str]:
    """Retourne les keywords trouvés dans les textes."""
    found = []
    for kw in keywords:
        pattern = re.compile(r"\b" + re.escape(kw) + r"(s|es|ée|er)?\b", re.IGNORECASE)
        if any(pattern.search(t) for t in texts):
            found.append(kw)
    return found


class AllergyFilter:
    """Filtre les recettes incompatibles avec les profils du foyer."""

    def is_safe_for_medical_conditions(self, recipe: dict, member: MemberProfile) -> tuple[bool, str]:
        """
        Vérifie si la recette est compatible avec les pathologies médicales du membre.
        Retourne (safe, reason).
        """
        if not member.medical_conditions:
            return True, ""

        texts = _ingredient_texts(recipe)
        full_text = " ".join(texts)

        for condition in member.medical_conditions:
            keywords = MEDICAL_KEYWORDS.get(condition, [])
            found = _contains(texts, keywords)
            if found:
                return False, f"pathologie {condition.value}: {', '.join(found[:3])}"

        return True, ""

    def is_safe_for_member(self, recipe: dict, member: MemberProfile) -> tuple[bool, str]:
        """
        Retourne (safe, reason).
        safe=False si la recette contient un allergène, restriction alimentaire ou ingrédient incompatible avec une pathologie.
        """
        texts = _ingredient_texts(recipe)
        full_text = " ".join(texts)

        for allergen in member.allergies:
            pattern = re.compile(r"\b" + re.escape(allergen.lower()) + r"\b", re.IGNORECASE)
            if pattern.search(full_text):
                return False, f"allergène détecté: {allergen}"

        for restriction in member.dietary_restrictions:
            keywords = RESTRICTION_KEYWORDS.get(restriction, [])
            found = _contains(texts, keywords)
            if found:
                return False, f"restriction {restriction.value}: {', '.join(found[:3])}"

        medical_safe, medical_reason = self.is_safe_for_medical_conditions(recipe, member)
        if not medical_safe:
            return False, medical_reason

        return True, ""

    def is_safe_for_household(self, recipe: dict, household: HouseholdProfile) -> tuple[bool, str]:
        """
        Retourne (safe, reason) en vérifiant tous les membres du foyer.
        La recette est rejetée si elle est incompatible avec au moins un membre.
        """
        for member in household.members:
            safe, reason = self.is_safe_for_member(recipe, member)
            if not safe:
                return False, f"{member.name}: {reason}"
        return True, ""

    def filter_recipes(
        self, recipes: list[dict], household: HouseholdProfile
    ) -> tuple[list[dict], list[tuple[dict, str]]]:
        """
        Partitionne en (recettes sûres, [(recette_rejetée, raison)]).
        """
        safe: list[dict] = []
        rejected: list[tuple[dict, str]] = []
        for recipe in recipes:
            ok, reason = self.is_safe_for_household(recipe, household)
            if ok:
                safe.append(recipe)
            else:
                rejected.append((recipe, reason))
        return safe, rejected
