"""Budget settings models."""

from __future__ import annotations

import re
from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator

_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class BudgetPeriod(BaseModel):
    """A single budget period (month)."""

    month: str = Field(..., description="Format 'YYYY-MM'")
    total_budget: float = Field(..., ge=0, description="Budget mensuel brut en €")
    condiments_forfait: float = Field(
        20.0,
        ge=0,
        description="Forfait mensuel pour condiments (huile, sel, épices...)",
    )

    @field_validator("month")
    @classmethod
    def _check_month(cls, value: str) -> str:
        if not _MONTH_RE.match(value):
            raise ValueError("month must match 'YYYY-MM'")
        return value

    @property
    def effective_budget(self) -> float:
        """Budget net après retrait du forfait condiments."""
        return max(0.0, self.total_budget - self.condiments_forfait)


class BudgetSettings(BaseModel):
    """Full budget configuration with per-meal/per-day derivation."""

    month: str = Field(..., description="Format 'YYYY-MM'")
    total_budget: float = Field(..., ge=0)
    condiments_forfait: float = Field(20.0, ge=0)
    currency: str = Field("EUR", min_length=3, max_length=3)
    meals_per_day: int = Field(3, ge=1, le=6)
    days_per_month: int = Field(30, ge=1, le=31)

    @field_validator("month")
    @classmethod
    def _check_month(cls, value: str) -> str:
        if not _MONTH_RE.match(value):
            raise ValueError("month must match 'YYYY-MM'")
        return value

    @field_validator("currency")
    @classmethod
    def _upper_currency(cls, value: str) -> str:
        return value.upper()

    @model_validator(mode="after")
    def _check_forfait(self) -> "BudgetSettings":
        if self.condiments_forfait > self.total_budget:
            raise ValueError("condiments_forfait cannot exceed total_budget")
        return self

    @property
    def effective_budget(self) -> float:
        return max(0.0, self.total_budget - self.condiments_forfait)

    @property
    def budget_per_meal(self) -> float:
        meals = max(1, self.meals_per_day * self.days_per_month)
        return self.effective_budget / meals

    @property
    def budget_per_day(self) -> float:
        return self.effective_budget / max(1, self.days_per_month)

    @classmethod
    def current_month(cls) -> str:
        today = date.today()
        return f"{today.year:04d}-{today.month:02d}"

    def to_period(self) -> BudgetPeriod:
        return BudgetPeriod(
            month=self.month,
            total_budget=self.total_budget,
            condiments_forfait=self.condiments_forfait,
        )
