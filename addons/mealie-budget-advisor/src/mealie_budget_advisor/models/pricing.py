"""Pricing source models."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PriceSource(str, Enum):
    """Source of a price datapoint."""

    open_prices = "open_prices"
    manual = "manual"
    estimated = "estimated"


class ManualPrice(BaseModel):
    """A user-curated price for a canonical ingredient name."""

    ingredient_name: str = Field(..., min_length=1, description="Nom normalisé (lowercase)")
    unit: str = Field(..., description="kg, l, unit, piece, ...")
    price_per_unit: float = Field(..., ge=0, description="Prix par unité de base")
    currency: str = Field("EUR", min_length=3, max_length=3)
    source: PriceSource = PriceSource.manual
    note: Optional[str] = None
    updated_at: date = Field(default_factory=date.today)


class OpenPrice(BaseModel):
    """A price datapoint returned by the Open Prices API."""

    product_name: Optional[str] = None
    product_code: Optional[str] = None
    price: float = Field(..., ge=0)
    currency: str = "EUR"
    store: Optional[str] = None
    location: Optional[str] = None
    collected_at: Optional[datetime] = None
    source: PriceSource = PriceSource.open_prices
