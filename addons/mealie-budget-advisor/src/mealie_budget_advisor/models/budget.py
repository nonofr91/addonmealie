"""Modèles pour la gestion du budget mensuel."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, computed_field


class BudgetPeriod(BaseModel):
    """Représente une période budgétaire (mois)."""

    year: int = Field(..., description="Année (ex: 2026)")
    month: int = Field(..., ge=1, le=12, description="Mois (1-12)")

    @property
    def period_label(self) -> str:
        """Retourne le label de la période (YYYY-MM)."""
        return f"{self.year:04d}-{self.month:02d}"

    @classmethod
    def from_string(cls, period_str: str) -> "BudgetPeriod":
        """Parse une période au format YYYY-MM."""
        year, month = map(int, period_str.split("-"))
        return cls(year=year, month=month)

    @classmethod
    def current(cls) -> "BudgetPeriod":
        """Retourne la période actuelle."""
        now = datetime.now()
        return cls(year=now.year, month=now.month)


class BudgetSettings(BaseModel):
    """Paramètres de budget mensuel avec forfait condiments."""

    period: BudgetPeriod = Field(default_factory=BudgetPeriod.current)
    total_budget: float = Field(
        ..., gt=0, description="Budget brut mensuel en € (ce que l'utilisateur déclare)"
    )
    condiments_forfait: float = Field(
        default=20.0,
        ge=0,
        description="Forfaitaire pour petites quantités (huile, sel, épices) en €"
    )
    currency: str = Field(default="EUR", description="Devise (EUR par défaut)")
    meals_per_day: int = Field(default=3, ge=1, le=6, description="Nombre de repas par jour")
    days_per_month: int = Field(default=30, ge=1, le=31, description="Jours dans le mois")

    notes: Optional[str] = Field(
        default=None, description="Notes optionnelles sur le budget"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default=None)

    @computed_field
    @property
    def effective_budget(self) -> float:
        """Budget net après déduction du forfait condiments."""
        return max(0.0, self.total_budget - self.condiments_forfait)

    @computed_field
    @property
    def budget_per_meal(self) -> float:
        """Budget moyen par repas."""
        total_meals = self.days_per_month * self.meals_per_day
        if total_meals == 0:
            return 0.0
        return round(self.effective_budget / total_meals, 2)

    @computed_field
    @property
    def budget_per_day(self) -> float:
        """Budget moyen par jour."""
        if self.days_per_month == 0:
            return 0.0
        return round(self.effective_budget / self.days_per_month, 2)

    class Config:
        populate_by_name = True
