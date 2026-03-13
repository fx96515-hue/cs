"""
Bulk Import Tools for Historical Data
CSV upload and processing for Freight, Price, Weather data
"""

import logging
import csv
import json
from io import StringIO
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ImportStats:
    """Statistics for import operation"""
    total_rows: int
    valid_rows: int
    rejected_rows: int
    duplicates: int
    errors: List[str]
    validation_time_ms: int


class FreightCSVImporter:
    """Import freight historical data from CSV"""
    
    REQUIRED_COLUMNS = [
        "route_name", "container_type", "weight_kg", "year_shipped", 
        "season", "fuel_cost_per_kg", "reliability_score", "carrier"
    ]
    
    @staticmethod
    def validate_row(row: Dict) -> Tuple[bool, Optional[str]]:
        """Validate freight CSV row"""
        try:
            # Check required fields
            for col in FreightCSVImporter.REQUIRED_COLUMNS:
                if col not in row or row[col] is None:
                    return False, f"Missing required field: {col}"
            
            # Validate types
            float(row["weight_kg"])
            float(row["fuel_cost_per_kg"])
            float(row["reliability_score"])
            int(row["year_shipped"])
            
            # Validate ranges
            if not (0 <= float(row["reliability_score"]) <= 1):
                return False, "reliability_score must be 0-1"
            
            return True, None
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def import_csv(csv_content: str, skip_duplicates: bool = True) -> ImportStats:
        """Import freight data from CSV"""
        stats = ImportStats(
            total_rows=0,
            valid_rows=0,
            rejected_rows=0,
            duplicates=0,
            errors=[],
            validation_time_ms=0
        )
        
        try:
            start_time = datetime.utcnow()
            
            reader = csv.DictReader(StringIO(csv_content))
            if not reader.fieldnames:
                stats.errors.append("Empty CSV or no headers")
                return stats
            
            seen_routes = set()
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
                stats.total_rows += 1
                
                # Check duplicates
                route_key = row.get("route_name")
                if route_key in seen_routes:
                    stats.duplicates += 1
                    if skip_duplicates:
                        continue
                seen_routes.add(route_key)
                
                # Validate
                is_valid, error = FreightCSVImporter.validate_row(row)
                if not is_valid:
                    stats.rejected_rows += 1
                    stats.errors.append(f"Row {row_num}: {error}")
                    continue
                
                # Valid row
                stats.valid_rows += 1
            
            elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
            stats.validation_time_ms = int(elapsed)
            
            logger.info(f"Freight import: {stats.valid_rows} valid, {stats.rejected_rows} rejected")
            return stats
        
        except Exception as e:
            logger.error(f"Freight CSV import error: {str(e)}")
            stats.errors.append(str(e))
            return stats


class PriceCSVImporter:
    """Import coffee price historical data from CSV"""
    
    REQUIRED_COLUMNS = [
        "origin", "variety", "process_method", "quality_grade",
        "price_low_usd_lb", "price_high_usd_lb", "date_recorded"
    ]
    
    @staticmethod
    def validate_row(row: Dict) -> Tuple[bool, Optional[str]]:
        """Validate price CSV row"""
        try:
            for col in PriceCSVImporter.REQUIRED_COLUMNS:
                if col not in row or row[col] is None:
                    return False, f"Missing required field: {col}"
            
            # Validate price ranges
            low_price = float(row["price_low_usd_lb"])
            high_price = float(row["price_high_usd_lb"])
            
            if low_price < 0 or high_price < 0:
                return False, "Prices cannot be negative"
            
            if low_price > high_price:
                return False, "Low price cannot exceed high price"
            
            # Validate date
            datetime.strptime(row["date_recorded"], "%Y-%m-%d")
            
            return True, None
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def import_csv(csv_content: str) -> ImportStats:
        """Import price data from CSV"""
        stats = ImportStats(
            total_rows=0,
            valid_rows=0,
            rejected_rows=0,
            duplicates=0,
            errors=[],
            validation_time_ms=0
        )
        
        try:
            start_time = datetime.utcnow()
            
            reader = csv.DictReader(StringIO(csv_content))
            if not reader.fieldnames:
                stats.errors.append("Empty CSV or no headers")
                return stats
            
            seen_records = set()
            
            for row_num, row in enumerate(reader, start=2):
                stats.total_rows += 1
                
                # Check duplicates
                record_key = f"{row.get('origin')}_{row.get('variety')}_{row.get('date_recorded')}"
                if record_key in seen_records:
                    stats.duplicates += 1
                    continue
                seen_records.add(record_key)
                
                # Validate
                is_valid, error = PriceCSVImporter.validate_row(row)
                if not is_valid:
                    stats.rejected_rows += 1
                    stats.errors.append(f"Row {row_num}: {error}")
                    continue
                
                stats.valid_rows += 1
            
            elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
            stats.validation_time_ms = int(elapsed)
            
            logger.info(f"Price import: {stats.valid_rows} valid, {stats.rejected_rows} rejected")
            return stats
        
        except Exception as e:
            logger.error(f"Price CSV import error: {str(e)}")
            stats.errors.append(str(e))
            return stats


class WeatherCSVImporter:
    """Import weather data from CSV"""
    
    REQUIRED_COLUMNS = [
        "region", "observation_date", "temp_min_c", "temp_max_c",
        "precipitation_mm", "source"
    ]
    
    @staticmethod
    def validate_row(row: Dict) -> Tuple[bool, Optional[str]]:
        """Validate weather CSV row"""
        try:
            for col in WeatherCSVImporter.REQUIRED_COLUMNS:
                if col not in row or row[col] is None:
                    return False, f"Missing required field: {col}"
            
            # Validate temperatures
            float(row["temp_min_c"])
            float(row["temp_max_c"])
            float(row["precipitation_mm"])
            
            # Validate date
            datetime.strptime(row["observation_date"], "%Y-%m-%d")
            
            return True, None
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def import_csv(csv_content: str) -> ImportStats:
        """Import weather data from CSV"""
        stats = ImportStats(
            total_rows=0,
            valid_rows=0,
            rejected_rows=0,
            duplicates=0,
            errors=[],
            validation_time_ms=0
        )
        
        try:
            start_time = datetime.utcnow()
            
            reader = csv.DictReader(StringIO(csv_content))
            if not reader.fieldnames:
                stats.errors.append("Empty CSV or no headers")
                return stats
            
            seen_records = set()
            
            for row_num, row in enumerate(reader, start=2):
                stats.total_rows += 1
                
                # Check duplicates
                record_key = f"{row.get('region')}_{row.get('observation_date')}"
                if record_key in seen_records:
                    stats.duplicates += 1
                    continue
                seen_records.add(record_key)
                
                # Validate
                is_valid, error = WeatherCSVImporter.validate_row(row)
                if not is_valid:
                    stats.rejected_rows += 1
                    stats.errors.append(f"Row {row_num}: {error}")
                    continue
                
                stats.valid_rows += 1
            
            elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
            stats.validation_time_ms = int(elapsed)
            
            logger.info(f"Weather import: {stats.valid_rows} valid, {stats.rejected_rows} rejected")
            return stats
        
        except Exception as e:
            logger.error(f"Weather CSV import error: {str(e)}")
            stats.errors.append(str(e))
            return stats


class BulkImportManager:
    """Unified bulk import manager"""
    
    @staticmethod
    def import_data(
        csv_content: str,
        data_type: str,
        skip_duplicates: bool = True
    ) -> Dict:
        """
        Import data from CSV
        
        Args:
            csv_content: CSV string content
            data_type: "freight", "price", or "weather"
            skip_duplicates: Skip duplicate records
        
        Returns:
            Import result with statistics
        """
        
        if data_type == "freight":
            stats = FreightCSVImporter.import_csv(csv_content, skip_duplicates)
        elif data_type == "price":
            stats = PriceCSVImporter.import_csv(csv_content)
        elif data_type == "weather":
            stats = WeatherCSVImporter.import_csv(csv_content)
        else:
            return {
                "status": "error",
                "message": f"Unknown data type: {data_type}",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return {
            "status": "completed" if stats.errors else "completed",
            "data_type": data_type,
            "total_rows": stats.total_rows,
            "valid_rows": stats.valid_rows,
            "rejected_rows": stats.rejected_rows,
            "duplicates_skipped": stats.duplicates,
            "validation_time_ms": stats.validation_time_ms,
            "errors": stats.errors[:10],  # Limit to 10 errors
            "timestamp": datetime.utcnow().isoformat()
        }
