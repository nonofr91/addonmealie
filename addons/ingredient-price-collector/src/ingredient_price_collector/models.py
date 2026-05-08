from datetime import date, datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class PriceSource(str, Enum):
    manual_import = "manual_import"
    open_prices = "open_prices"
    insee_ipc = "insee_ipc"
    rnm_franceagrimer = "rnm_franceagrimer"
    ai_estimate = "ai_estimate"
    unknown = "unknown"


class PriceObservationCreate(BaseModel):
    ingredient_name: str = Field(min_length=1)
    product_name: str | None = None
    barcode: str | None = None
    source: PriceSource = PriceSource.manual_import
    source_url: str | None = None
    store_name: str | None = None
    store_location: str | None = None
    observed_at: date | None = None
    price_amount: float = Field(gt=0)
    currency: str = "EUR"
    package_quantity: float = Field(gt=0)
    package_unit: str = Field(min_length=1)
    confidence: float | None = Field(default=None, ge=0, le=1)
    raw_payload: dict[str, Any] | None = None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper().strip()

    @field_validator("package_unit")
    @classmethod
    def normalize_package_unit(cls, value: str) -> str:
        return value.lower().strip()


class PriceObservation(PriceObservationCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    normalized_ingredient: str
    price_per_kg: float | None = None
    price_per_l: float | None = None
    price_per_piece: float | None = None
    quality_flags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PriceRecommendation(BaseModel):
    ingredient_name: str
    normalized_ingredient: str
    recommended_price: float | None = None
    recommended_unit: str | None = None
    source: str | None = None
    confidence: float = 0
    reason: str
    observed_at: date | None = None
    valid_until: date | None = None
    alternatives: list[PriceObservation] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ImportResult(BaseModel):
    imported: int
    rejected: int
    observations: list[PriceObservation] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
