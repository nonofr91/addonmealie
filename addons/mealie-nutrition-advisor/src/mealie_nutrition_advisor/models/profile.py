"""Household member profile models."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Sex(str, Enum):
    male = "male"
    female = "female"


class ActivityLevel(str, Enum):
    sedentary = "sedentary"          # Peu ou pas d'exercice
    lightly_active = "lightly_active"  # Exercice léger 1-3 j/sem
    moderately_active = "moderately_active"  # Exercice modéré 3-5 j/sem
    very_active = "very_active"      # Exercice intense 6-7 j/sem
    extra_active = "extra_active"    # Très intense / travail physique


ACTIVITY_PAL: dict[ActivityLevel, float] = {
    ActivityLevel.sedentary: 1.2,
    ActivityLevel.lightly_active: 1.375,
    ActivityLevel.moderately_active: 1.55,
    ActivityLevel.very_active: 1.725,
    ActivityLevel.extra_active: 1.9,
}


class Goal(str, Enum):
    weight_loss = "weight_loss"
    maintenance = "maintenance"
    muscle_gain = "muscle_gain"


GOAL_CALORIE_FACTOR: dict[Goal, float] = {
    Goal.weight_loss: 0.80,    # -20% du TDEE
    Goal.maintenance: 1.00,
    Goal.muscle_gain: 1.10,   # +10% du TDEE
}


class DietaryRestriction(str, Enum):
    vegetarian = "vegetarian"
    vegan = "vegan"
    gluten_free = "gluten_free"
    lactose_free = "lactose_free"
    halal = "halal"
    kosher = "kosher"
    low_fodmap = "low_fodmap"


class MedicalCondition(str, Enum):
    """Pathologies médicales courantes impactant l'alimentation."""
    diabetes = "diabetes"
    hypertension = "hypertension"
    high_cholesterol = "high_cholesterol"
    gout = "gout"
    gerd = "gerd"  # Reflux gastrique
    kidney_disease = "kidney_disease"


class MacroTargets(BaseModel):
    """Cibles nutritionnelles journalières personnalisées."""

    calories_per_day: Optional[float] = Field(None, ge=0, description="Calories/jour (calculées si absent)")
    protein_g_per_day: Optional[float] = Field(None, ge=0, description="Protéines cibles g/jour")
    fat_pct_max: Optional[float] = Field(None, ge=0, le=100, description="% calories lipides max")
    carb_pct_max: Optional[float] = Field(None, ge=0, le=100, description="% calories glucides max")
    fiber_g_per_day: Optional[float] = Field(None, ge=0, description="Fibres cibles g/jour")
    sodium_mg_per_day_max: Optional[float] = Field(None, ge=0, description="Sodium max mg/jour")


class DayOfWeek(str, Enum):
    """Jours de la semaine."""
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"
    sunday = "sunday"


class WeeklyPresencePattern(BaseModel):
    """Pattern de présence hebdomadaire d'un membre."""

    presence: dict[DayOfWeek, list[str]] = Field(
        default_factory=lambda: {
            day: ["breakfast", "lunch", "dinner"] for day in DayOfWeek
        },
        description="Mapping jour → liste des repas pris (breakfast/lunch/dinner)",
    )

    def is_present(self, day: DayOfWeek, meal_type: str) -> bool:
        """Vérifie si le membre est présent à un repas donné."""
        return meal_type in self.presence.get(day, [])

    def get_present_days(self) -> list[DayOfWeek]:
        """Retourne les jours où le membre prend au moins un repas."""
        return [day for day, meals in self.presence.items() if meals]

    def meals_per_day(self, day: DayOfWeek) -> int:
        """Nombre de repas pris un jour donné."""
        return len(self.presence.get(day, []))


class MemberProfile(BaseModel):
    """Profil complet d'un membre du foyer."""

    name: str = Field(..., min_length=1)
    age: int = Field(..., ge=1, le=120)
    sex: Sex
    weight_kg: float = Field(..., gt=0, le=500)
    height_cm: float = Field(..., gt=0, le=300)
    activity_level: ActivityLevel = ActivityLevel.moderately_active
    goal: Goal = Goal.maintenance
    dietary_restrictions: list[DietaryRestriction] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list, description="Liste d'allergènes en texte libre")
    foods_to_avoid: list[str] = Field(default_factory=list, description="Liste d'aliments à éviter (préférences personnelles, digestion, etc.)")
    medical_conditions: list[MedicalCondition] = Field(default_factory=list, description="Pathologies médicales")
    weekly_presence: WeeklyPresencePattern = Field(default_factory=WeeklyPresencePattern)
    custom_targets: MacroTargets = Field(default_factory=MacroTargets)

    def bmr(self) -> float:
        """Calcul du BMR via formule Mifflin-St Jeor (kcal/jour)."""
        if self.sex == Sex.male:
            return 10 * self.weight_kg + 6.25 * self.height_cm - 5 * self.age + 5
        else:
            return 10 * self.weight_kg + 6.25 * self.height_cm - 5 * self.age - 161

    def tdee(self) -> float:
        """Total Daily Energy Expenditure = BMR × PAL."""
        pal = ACTIVITY_PAL[self.activity_level]
        return round(self.bmr() * pal, 0)

    def target_calories(self) -> float:
        """Calories cibles selon l'objectif (ou valeur custom si définie)."""
        if self.custom_targets.calories_per_day is not None:
            return self.custom_targets.calories_per_day
        return round(self.tdee() * GOAL_CALORIE_FACTOR[self.goal], 0)

    def recommended_protein_g(self) -> float:
        """Protéines recommandées : 0.8–2.0 g/kg selon l'objectif."""
        if self.custom_targets.protein_g_per_day is not None:
            return self.custom_targets.protein_g_per_day
        factor = {Goal.weight_loss: 1.5, Goal.maintenance: 0.8, Goal.muscle_gain: 2.0}[self.goal]
        return round(self.weight_kg * factor, 0)

    def recommended_sodium_mg(self) -> float:
        """Sodium recommandé : ajusté selon les pathologies."""
        if self.custom_targets.sodium_mg_per_day_max is not None:
            return self.custom_targets.sodium_mg_per_day_max

        base_sodium = 2300.0
        if MedicalCondition.hypertension in self.medical_conditions:
            base_sodium = 1500.0
        elif MedicalCondition.kidney_disease in self.medical_conditions:
            base_sodium = 2000.0
        return base_sodium

    def recommended_fat_g(self) -> float:
        """Lipides recommandés : 25–35% des calories cibles."""
        pct = self.custom_targets.fat_pct_max or 30.0
        return round(self.target_calories() * (pct / 100.0) / 9.0, 0)

    def recommended_carb_g(self) -> float:
        """Glucides recommandés : calories restantes après protéines et lipides, ajusté selon pathologies."""
        protein_kcal = self.recommended_protein_g() * 4
        fat_kcal = self.recommended_fat_g() * 9
        carb_kcal = max(self.target_calories() - protein_kcal - fat_kcal, 0)

        if self.custom_targets.carb_pct_max:
            carb_kcal = min(carb_kcal, self.target_calories() * self.custom_targets.carb_pct_max / 100.0)

        if MedicalCondition.diabetes in self.medical_conditions:
            carb_kcal = min(carb_kcal, self.target_calories() * 0.45)

        return round(carb_kcal / 4.0, 0)

    def summary(self) -> dict:
        """Résumé lisible des besoins nutritionnels."""
        return {
            "name": self.name,
            "bmr_kcal": round(self.bmr(), 0),
            "tdee_kcal": self.tdee(),
            "target_calories_kcal": self.target_calories(),
            "recommended_protein_g": self.recommended_protein_g(),
            "recommended_fat_g": self.recommended_fat_g(),
            "recommended_carb_g": self.recommended_carb_g(),
            "goal": self.goal.value,
            "restrictions": [r.value for r in self.dietary_restrictions],
            "allergies": self.allergies,
        }


class HouseholdProfile(BaseModel):
    """Foyer : ensemble des profils membres."""

    household_name: str = "Mon foyer"
    members: list[MemberProfile] = Field(default_factory=list)

    def aggregate_daily_calories(self) -> float:
        """Calories totales journalières pour tous les membres."""
        return sum(m.target_calories() for m in self.members)

    def all_allergies(self) -> set[str]:
        """Union de toutes les allergies du foyer (en minuscules)."""
        result: set[str] = set()
        for m in self.members:
            result.update(a.lower() for a in m.allergies)
        return result

    def all_restrictions(self) -> set[DietaryRestriction]:
        """Union de toutes les restrictions alimentaires du foyer."""
        result: set[DietaryRestriction] = set()
        for m in self.members:
            result.update(m.dietary_restrictions)
        return result
