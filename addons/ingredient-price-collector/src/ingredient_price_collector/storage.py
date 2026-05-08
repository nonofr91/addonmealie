import json
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .models import PriceObservation


class PriceStorage:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS price_observations (
                    id TEXT PRIMARY KEY,
                    ingredient_name TEXT NOT NULL,
                    normalized_ingredient TEXT NOT NULL,
                    product_name TEXT,
                    barcode TEXT,
                    source TEXT NOT NULL,
                    source_url TEXT,
                    store_name TEXT,
                    store_location TEXT,
                    observed_at TEXT,
                    price_amount REAL NOT NULL,
                    currency TEXT NOT NULL,
                    package_quantity REAL NOT NULL,
                    package_unit TEXT NOT NULL,
                    price_per_kg REAL,
                    price_per_l REAL,
                    price_per_piece REAL,
                    confidence REAL NOT NULL,
                    quality_flags TEXT NOT NULL,
                    raw_payload TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_price_observations_normalized ON price_observations(normalized_ingredient)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_price_observations_quality ON price_observations(confidence, observed_at)"
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at)"
            )

    def add_observations(self, observations: list[PriceObservation]) -> None:
        with self._connect() as connection:
            connection.executemany(
                """
                INSERT OR REPLACE INTO price_observations (
                    id, ingredient_name, normalized_ingredient, product_name, barcode, source,
                    source_url, store_name, store_location, observed_at, price_amount, currency,
                    package_quantity, package_unit, price_per_kg, price_per_l, price_per_piece,
                    confidence, quality_flags, raw_payload, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [self._to_row(observation) for observation in observations],
            )

    def search(self, normalized_ingredient: str, unit: str | None = None, store: str | None = None) -> list[PriceObservation]:
        clauses = ["normalized_ingredient = ?"]
        params: list[str] = [normalized_ingredient]
        if store:
            clauses.append("lower(coalesce(store_name, '')) = lower(?)")
            params.append(store)
        if unit == "kg":
            clauses.append("price_per_kg IS NOT NULL")
        elif unit == "l":
            clauses.append("price_per_l IS NOT NULL")
        elif unit in {"piece", "unit"}:
            clauses.append("price_per_piece IS NOT NULL")

        query = f"""
            SELECT * FROM price_observations
            WHERE {' AND '.join(clauses)}
            ORDER BY confidence DESC, observed_at DESC, created_at DESC
            LIMIT 20
        """
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._from_row(row) for row in rows]

    def anomalies(self, limit: int = 100) -> list[PriceObservation]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM price_observations
                WHERE quality_flags != '[]'
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def count_observations(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT count(*) AS count FROM price_observations").fetchone()
        return int(row["count"])

    def cache_get(self, key: str) -> dict | None:
        self._cleanup_expired_cache()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT value, expires_at FROM cache WHERE key = ? AND expires_at > ?",
                (key, datetime.now(timezone.utc).isoformat()),
            ).fetchone()
            if row:
                return json.loads(row["value"])
            return None

    def cache_set(self, key: str, value: dict, ttl_hours: int = 24) -> None:
        expires_at = datetime.now(timezone.utc).replace(microsecond=0) + datetime.timedelta(hours=ttl_hours)
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
                (key, json.dumps(value, ensure_ascii=False), expires_at.isoformat()),
            )

    def _cleanup_expired_cache(self) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM cache WHERE expires_at < ?",
                (datetime.now(timezone.utc).isoformat(),),
            )

    def _to_row(self, observation: PriceObservation) -> tuple:
        return (
            observation.id,
            observation.ingredient_name,
            observation.normalized_ingredient,
            observation.product_name,
            observation.barcode,
            observation.source.value,
            observation.source_url,
            observation.store_name,
            observation.store_location,
            observation.observed_at.isoformat() if observation.observed_at else None,
            observation.price_amount,
            observation.currency,
            observation.package_quantity,
            observation.package_unit,
            observation.price_per_kg,
            observation.price_per_l,
            observation.price_per_piece,
            observation.confidence,
            json.dumps(observation.quality_flags, ensure_ascii=False),
            json.dumps(observation.raw_payload, ensure_ascii=False) if observation.raw_payload else None,
            observation.created_at.isoformat(),
        )

    def _from_row(self, row: sqlite3.Row) -> PriceObservation:
        payload = dict(row)
        payload["quality_flags"] = json.loads(payload["quality_flags"] or "[]")
        payload["raw_payload"] = json.loads(payload["raw_payload"]) if payload["raw_payload"] else None
        payload["observed_at"] = date.fromisoformat(payload["observed_at"]) if payload["observed_at"] else None
        payload["created_at"] = datetime.fromisoformat(payload["created_at"])
        return PriceObservation(**payload)
