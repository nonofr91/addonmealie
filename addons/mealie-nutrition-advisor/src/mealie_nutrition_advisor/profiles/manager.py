"""Household profile manager — load, save, CRUD on household_profiles.json."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from ..models.profile import (
    ActivityLevel,
    DietaryRestriction,
    Goal,
    HouseholdProfile,
    MacroTargets,
    MemberProfile,
    Sex,
)

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "config" / "household_profiles.json"


class ProfileManager:
    """Gestionnaire des profils du foyer."""

    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
        self._household: HouseholdProfile | None = None

    def load(self) -> HouseholdProfile:
        """Charge les profils depuis le fichier JSON (crée un foyer vide si absent)."""
        if not self.config_path.exists():
            logger.warning("Fichier profils introuvable: %s — foyer vide créé", self.config_path)
            self._household = HouseholdProfile()
            return self._household

        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
            self._household = HouseholdProfile.model_validate(data)
            logger.info("Profils chargés: %d membre(s) — %s", len(self._household.members), self.config_path)
        except Exception as exc:
            logger.error("Erreur chargement profils: %s", exc)
            self._household = HouseholdProfile()
        return self._household

    def save(self, household: HouseholdProfile | None = None) -> None:
        """Sauvegarde les profils dans le fichier JSON."""
        target = household or self._household
        if target is None:
            raise ValueError("Aucun profil à sauvegarder")
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(
            target.model_dump_json(indent=2),
            encoding="utf-8",
        )
        logger.info("Profils sauvegardés: %s", self.config_path)

    @property
    def household(self) -> HouseholdProfile:
        if self._household is None:
            self.load()
        assert self._household is not None
        return self._household

    def get_member(self, name: str) -> MemberProfile | None:
        """Retourne un membre par son nom (insensible à la casse)."""
        for m in self.household.members:
            if m.name.lower() == name.lower():
                return m
        return None

    def add_member(self, member: MemberProfile) -> None:
        """Ajoute un membre (remplace si même nom)."""
        existing = self.get_member(member.name)
        if existing:
            idx = self.household.members.index(existing)
            self.household.members[idx] = member
            logger.info("Profil mis à jour: %s", member.name)
        else:
            self.household.members.append(member)
            logger.info("Nouveau membre ajouté: %s", member.name)
        self.save()

    def remove_member(self, name: str) -> bool:
        """Supprime un membre. Retourne True si trouvé et supprimé."""
        member = self.get_member(name)
        if member:
            self.household.members.remove(member)
            self.save()
            logger.info("Membre supprimé: %s", name)
            return True
        return False

    def print_summary(self) -> None:
        """Affiche un résumé des profils du foyer."""
        h = self.household
        print(f"\n🏠  {h.household_name}")
        print(f"    {len(h.members)} membre(s) — {round(h.aggregate_daily_calories())} kcal/jour total\n")
        for m in h.members:
            s = m.summary()
            print(f"  👤 {s['name']} ({m.age} ans, {m.sex.value}, {m.weight_kg} kg, {m.height_cm} cm)")
            print(f"     BMR: {s['bmr_kcal']} kcal | TDEE: {s['tdee_kcal']} kcal | Cible: {s['target_calories_kcal']} kcal")
            print(f"     Protéines: {s['recommended_protein_g']}g | Lipides: {s['recommended_fat_g']}g | Glucides: {s['recommended_carb_g']}g")
            if s["restrictions"]:
                print(f"     Régimes: {', '.join(s['restrictions'])}")
            if s["allergies"]:
                print(f"     Allergies: {', '.join(s['allergies'])}")
            print()

    def interactive_add(self) -> MemberProfile:
        """Ajout interactif d'un membre via stdin."""
        print("\n➕  Ajout d'un nouveau membre\n")
        name = input("Nom : ").strip()
        age = int(input("Âge : "))
        sex_raw = input("Sexe (male/female) : ").strip().lower()
        sex = Sex(sex_raw)
        weight = float(input("Poids (kg) : "))
        height = float(input("Taille (cm) : "))

        print(f"Niveau d'activité : {[a.value for a in ActivityLevel]}")
        activity_raw = input("Activité (défaut: moderately_active) : ").strip() or "moderately_active"
        activity = ActivityLevel(activity_raw)

        print(f"Objectif : {[g.value for g in Goal]}")
        goal_raw = input("Objectif (défaut: maintenance) : ").strip() or "maintenance"
        goal = Goal(goal_raw)

        allergies_raw = input("Allergies (virgule-séparées, vide si aucune) : ").strip()
        allergies = [a.strip() for a in allergies_raw.split(",") if a.strip()]

        member = MemberProfile(
            name=name,
            age=age,
            sex=sex,
            weight_kg=weight,
            height_cm=height,
            activity_level=activity,
            goal=goal,
            allergies=allergies,
        )
        self.add_member(member)
        print(f"\n✅  {name} ajouté(e). Cible: {member.target_calories()} kcal/jour")
        return member
