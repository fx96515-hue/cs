"""
CSV bulk import validation helpers derived from PR721.

These helpers validate incoming CSV payloads before they are handed to the
current persistence services.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from io import StringIO


@dataclass
class ImportStats:
    total_rows: int
    valid_rows: int
    rejected_rows: int
    duplicates: int
    errors: list[str]
    validation_time_ms: int


class FreightCSVImporter:
    REQUIRED_COLUMNS = [
        "route",
        "origin_port",
        "destination_port",
        "carrier",
        "container_type",
        "weight_kg",
        "freight_cost_usd",
        "transit_days",
        "departure_date",
        "arrival_date",
        "season",
    ]

    @staticmethod
    def validate_row(row: dict) -> tuple[bool, str | None]:
        try:
            for column in FreightCSVImporter.REQUIRED_COLUMNS:
                if column not in row or row[column] is None or row[column] == "":
                    return False, f"Missing required field: {column}"
            float(row["weight_kg"])
            float(row["freight_cost_usd"])
            int(row["transit_days"])
            datetime.strptime(row["departure_date"], "%Y-%m-%d")
            datetime.strptime(row["arrival_date"], "%Y-%m-%d")
            return True, None
        except Exception as exc:
            return False, str(exc)


class PriceCSVImporter:
    REQUIRED_COLUMNS = [
        "date",
        "origin_country",
        "origin_region",
        "variety",
        "process_method",
        "quality_grade",
        "price_usd_per_kg",
        "price_usd_per_lb",
        "ice_c_price_usd_per_lb",
        "differential_usd_per_lb",
        "market_source",
    ]

    @staticmethod
    def validate_row(row: dict) -> tuple[bool, str | None]:
        try:
            for column in PriceCSVImporter.REQUIRED_COLUMNS:
                if column not in row or row[column] is None or row[column] == "":
                    return False, f"Missing required field: {column}"
            if float(row["price_usd_per_kg"]) < 0 or float(row["price_usd_per_lb"]) < 0:
                return False, "Prices cannot be negative"
            datetime.strptime(row["date"], "%Y-%m-%d")
            return True, None
        except Exception as exc:
            return False, str(exc)


class WeatherCSVImporter:
    REQUIRED_COLUMNS = [
        "region",
        "observation_date",
        "temp_min_c",
        "temp_max_c",
        "precipitation_mm",
        "source",
    ]

    @staticmethod
    def validate_row(row: dict) -> tuple[bool, str | None]:
        try:
            for column in WeatherCSVImporter.REQUIRED_COLUMNS:
                if column not in row or row[column] is None or row[column] == "":
                    return False, f"Missing required field: {column}"
            float(row["temp_min_c"])
            float(row["temp_max_c"])
            float(row["precipitation_mm"])
            datetime.strptime(row["observation_date"], "%Y-%m-%d")
            return True, None
        except Exception as exc:
            return False, str(exc)


class BulkImportManager:
    @staticmethod
    def _base_stats() -> ImportStats:
        return ImportStats(
            total_rows=0,
            valid_rows=0,
            rejected_rows=0,
            duplicates=0,
            errors=[],
            validation_time_ms=0,
        )

    @staticmethod
    def import_data(csv_content: str, data_type: str) -> dict:
        stats = BulkImportManager._base_stats()
        start_time = datetime.utcnow()

        reader = csv.DictReader(StringIO(csv_content))
        if not reader.fieldnames:
            stats.errors.append("Empty CSV or missing headers")
        else:
            seen: set[str] = set()
            for row_number, row in enumerate(reader, start=2):
                normalized = {
                    str(key).strip(): (value or "").strip()
                    for key, value in row.items()
                }
                if not any(normalized.values()):
                    continue

                stats.total_rows += 1
                duplicate_key = "|".join(normalized.values())
                if duplicate_key in seen:
                    stats.duplicates += 1
                    continue
                seen.add(duplicate_key)

                if data_type == "freight":
                    valid, error = FreightCSVImporter.validate_row(normalized)
                elif data_type == "price":
                    valid, error = PriceCSVImporter.validate_row(normalized)
                elif data_type == "weather":
                    valid, error = WeatherCSVImporter.validate_row(normalized)
                else:
                    return {
                        "status": "error",
                        "message": f"Unknown data type: {data_type}",
                        "timestamp": datetime.utcnow().isoformat(),
                    }

                if valid:
                    stats.valid_rows += 1
                else:
                    stats.rejected_rows += 1
                    stats.errors.append(f"Row {row_number}: {error}")

        stats.validation_time_ms = int(
            (datetime.utcnow() - start_time).total_seconds() * 1000
        )
        return {
            "status": "completed",
            "data_type": data_type,
            "total_rows": stats.total_rows,
            "valid_rows": stats.valid_rows,
            "rejected_rows": stats.rejected_rows,
            "duplicates_skipped": stats.duplicates,
            "validation_time_ms": stats.validation_time_ms,
            "errors": stats.errors[:10],
            "timestamp": datetime.utcnow().isoformat(),
        }
