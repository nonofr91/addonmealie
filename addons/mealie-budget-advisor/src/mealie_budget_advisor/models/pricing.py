"""Modèles pour les sources de prix."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PriceSource(str, Enum):
    """Source possible d'un prix."""

    OPEN_PRICES = "open_prices"
    MANUAL = "manual"
    ESTIMATED = "estimated"
    UNKNOWN = "unknown"


class ManualPrice(BaseModel):
    """Prix manuellement défini par l'utilisateur."""

    ingredient_name: str = Field(..., description="Nom normalisé de l'ingrédient")
    price_per_unit: float = Field(..., gt=0, description="Prix par unité de base (€)")
    unit: str = Field(..., description="Unité de base (kg, g, l, ml, unit)")
    store: Optional[str] = Field(default=None, description="Magasin où le prix a été observé")
    location: Optional[str] = Field(default=None, description="Localisation (ville/région)")
    notes: Optional[str] = Field(default=None, description="Notes additionnelles")
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True


class OpenPrice(BaseModel):
    """Prix provenant de l'API Open Prices (Open Food Facts)."""

    product_name: str = Field(..., description="Nom du produit")
    product_code: Optional[str] = Field(default=None, description="Code EAN/GTIN")
    price: float = Field(..., gt=0, description="Prix observé")
    currency: str = Field(default="EUR")
    quantity: float = Field(default=1.0, description="Quantité pour ce prix")
    unit: str = Field(default="unit", description="Unité (kg, g, l, ml, unit)")
    store_name: Optional[str] = Field(default=None)
    store_location: Optional[str] = Field(default=None)
    date_collected: Optional[datetime] = Field(default=None)
    source_url: Optional[str] = Field(default=None)

    @property
    def price_per_base_unit(self) -> float:
        """Calcule le prix par unité de base standardisée."""
        # Normaliser vers kg ou l
        unit_multipliers = {
            "kg": 1.0,
            "g": 1000.0,
            "l": 1.0,
            "ml": 1000.0,
            "cl": 100.0,
            "unit": 1.0,
        }
        multiplier = unit_multipliers.get(self.unit.lower(), 1.0)
        return round(self.price / self.quantity * multiplier, 4)
