import logging
from datetime import date, datetime, timezone
from typing import Any

import requests

from ..models import PriceObservation, PriceSource

logger = logging.getLogger(__name__)

INSEE_DATASET_ID = "6983dff81f90da358ccf74d8"
INSEE_RESOURCE_ID = "5961e778-380b-4098-9b7e-33697b44b3c6"
INSEE_CSV_URL = "https://api.insee.fr/melodi/file/DS_IPC_PRINC/DS_IPC_PRINC_CSV_FR"


class InseeIpcCollector:
    def __init__(self, csv_url: str | None = None) -> None:
        self.csv_url = csv_url or INSEE_CSV_URL
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "text/csv",
            "User-Agent": "Ingredient-Price-Collector/0.1.0",
        })

    def fetch_indices(self, year: int | None = None) -> list[dict[str, Any]]:
        try:
            response = self.session.get(self.csv_url, timeout=30)
            response.raise_for_status()
            content = response.text

            indices = self._parse_csv(content, year)
            logger.debug(f"INSEE IPC: {len(indices)} indices récupérés")
            return indices

        except requests.exceptions.RequestException as exc:
            logger.warning(f"Erreur INSEE IPC: {exc}")
            return []

    def _parse_csv(self, content: str, year: int | None) -> list[dict[str, Any]]:
        lines = content.splitlines()
        if len(lines) < 2:
            return []

        headers = lines[0].split(";")
        indices = []

        for line in lines[1:]:
            values = line.split(";")
            if len(values) != len(headers):
                continue

            row = dict(zip(headers, values))
            row_year = row.get("ANNEE")
            if year and row_year != str(year):
                continue

            indices.append(row)

        return indices

    def get_category_index(self, category_code: str, year: int | None = None) -> float | None:
        indices = self.fetch_indices(year)
        for index in indices:
            if index.get("COD_NAF") == category_code or index.get("COICOP") == category_code:
                try:
                    return float(index.get("INDICE", 0))
                except (ValueError, TypeError):
                    continue
        return None

    def create_observation_from_index(
        self,
        ingredient_name: str,
        category_code: str,
        base_price: float,
        base_unit: str,
        year: int | None = None,
    ) -> PriceObservation | None:
        index = self.get_category_index(category_code, year)
        if index is None:
            return None

        return PriceObservation(
            ingredient_name=ingredient_name,
            normalized_ingredient=ingredient_name.lower(),
            product_name=f"INSEE IPC {category_code}",
            source=PriceSource.insee_ipc,
            source_url=self.csv_url,
            observed_at=date(year if year else date.today().year, 1, 1),
            price_amount=base_price * (index / 100),
            currency="EUR",
            package_quantity=1,
            package_unit=base_unit,
            confidence=0.6,
            quality_flags=["index_based", "not_direct_price"],
            raw_payload={"category_code": category_code, "index": index},
            created_at=datetime.now(timezone.utc),
        )
