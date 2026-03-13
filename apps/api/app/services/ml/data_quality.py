"""
Data Quality Validation & Anomaly Detection
Ensures data integrity and detects outliers
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import statistics
import json

logger = logging.getLogger(__name__)

class DataQualityValidator:
    """Validates data quality and completeness"""
    
    @staticmethod
    def check_completeness(record: Dict, expected_fields: List[str]) -> Tuple[float, List[str]]:
        """
        Check data completeness (0-1)
        
        Returns:
            Tuple of (completeness_score, missing_fields)
        """
        missing = []
        for field in expected_fields:
            if field not in record or record[field] is None:
                missing.append(field)
        
        if not expected_fields:
            return 1.0, []
        
        completeness = (len(expected_fields) - len(missing)) / len(expected_fields)
        return completeness, missing
    
    @staticmethod
    def check_value_ranges(record: Dict, constraints: Dict[str, Tuple[float, float]]) -> Tuple[bool, List[str]]:
        """
        Check if values are within expected ranges
        
        Args:
            record: Data record
            constraints: Dict of field -> (min, max)
        
        Returns:
            Tuple of (all_valid, out_of_range_fields)
        """
        out_of_range = []
        
        for field, (min_val, max_val) in constraints.items():
            if field not in record:
                continue
            
            value = record[field]
            if value < min_val or value > max_val:
                out_of_range.append(f"{field}:{value} (expected {min_val}-{max_val})")
        
        return len(out_of_range) == 0, out_of_range
    
    @staticmethod
    def check_duplicates(records: List[Dict], key_fields: List[str]) -> Tuple[int, List[str]]:
        """
        Detect duplicate records
        
        Returns:
            Tuple of (duplicate_count, duplicate_keys)
        """
        seen = set()
        duplicates = []
        duplicate_count = 0
        
        for record in records:
            key = tuple(record.get(field) for field in key_fields)
            if key in seen:
                duplicates.append(str(key))
                duplicate_count += 1
            else:
                seen.add(key)
        
        return duplicate_count, duplicates[:10]  # Return first 10
    
    @staticmethod
    def check_temporal_consistency(records: List[Dict], date_field: str) -> Tuple[bool, List[str]]:
        """
        Check temporal consistency (dates in order)
        
        Returns:
            Tuple of (is_consistent, issues)
        """
        issues = []
        
        # Sort by date
        try:
            sorted_records = sorted(
                records,
                key=lambda r: r.get(date_field, "")
            )
            
            # Check for gaps
            prev_date = None
            for record in sorted_records:
                date_str = record.get(date_field)
                if date_str and prev_date:
                    if date_str < prev_date:
                        issues.append(f"Out of order: {prev_date} -> {date_str}")
                prev_date = date_str
        
        except Exception as e:
            issues.append(f"Date parsing error: {str(e)}")
        
        return len(issues) == 0, issues


class AnomalyDetector:
    """Detects outliers and anomalies in data"""
    
    @staticmethod
    def detect_statistical_outliers(
        values: List[float],
        method: str = "iqr",
        threshold: float = 1.5
    ) -> List[int]:
        """
        Detect statistical outliers
        
        Methods:
        - "iqr": Interquartile range method
        - "zscore": Z-score method (threshold = std devs)
        """
        if len(values) < 4:
            return []
        
        outliers = []
        
        if method == "iqr":
            sorted_vals = sorted(values)
            q1_idx = len(sorted_vals) // 4
            q3_idx = (3 * len(sorted_vals)) // 4
            
            q1 = sorted_vals[q1_idx]
            q3 = sorted_vals[q3_idx]
            iqr = q3 - q1
            
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr
            
            for idx, val in enumerate(values):
                if val < lower_bound or val > upper_bound:
                    outliers.append(idx)
        
        elif method == "zscore":
            mean = statistics.mean(values)
            try:
                stdev = statistics.stdev(values)
            except:
                return []
            
            for idx, val in enumerate(values):
                if stdev > 0:
                    zscore = abs((val - mean) / stdev)
                    if zscore > threshold:
                        outliers.append(idx)
        
        return outliers
    
    @staticmethod
    def detect_price_anomalies(price_history: List[Dict]) -> List[Dict]:
        """
        Detect anomalies in price data
        
        Checks for:
        - Sudden spikes/drops (>20% change)
        - Unusually flat prices (no variation)
        - Missing data points
        """
        anomalies = []
        
        if len(price_history) < 2:
            return anomalies
        
        prices = [p.get("price") for p in price_history if p.get("price") is not None]
        
        # Check for spikes
        for i in range(1, len(prices)):
            if prices[i-1] > 0:
                change = abs((prices[i] - prices[i-1]) / prices[i-1])
                if change > 0.20:
                    anomalies.append({
                        "type": "spike",
                        "index": i,
                        "previous_price": prices[i-1],
                        "current_price": prices[i],
                        "change_pct": change * 100
                    })
        
        # Check for flatness (no variation for >30 days)
        flat_start = 0
        for i in range(1, len(prices)):
            if prices[i] == prices[i-1]:
                if i - flat_start >= 30:
                    anomalies.append({
                        "type": "flat_period",
                        "start_index": flat_start,
                        "duration_days": i - flat_start,
                        "price": prices[i-1]
                    })
            else:
                flat_start = i
        
        return anomalies
    
    @staticmethod
    def detect_shipping_anomalies(shipping_records: List[Dict]) -> List[Dict]:
        """
        Detect anomalies in shipping data
        
        Checks for:
        - Unusual routes
        - Excessive delays
        - Unrealistic speeds
        """
        anomalies = []
        
        for idx, record in enumerate(shipping_records):
            # Check for unrealistic speeds (>50 knots is exceptional)
            if record.get("speed_knots", 0) > 50:
                anomalies.append({
                    "type": "excessive_speed",
                    "index": idx,
                    "speed_knots": record["speed_knots"]
                })
            
            # Check for excessive delays
            if record.get("delay_hours", 0) > 72:  # >3 days
                anomalies.append({
                    "type": "excessive_delay",
                    "index": idx,
                    "delay_hours": record["delay_hours"]
                })
            
            # Check for unusual routes (Peru to far distances)
            distance = record.get("distance_km", 0)
            if distance > 20000:
                anomalies.append({
                    "type": "unusual_route",
                    "index": idx,
                    "distance_km": distance
                })
        
        return anomalies
    
    @staticmethod
    def detect_weather_anomalies(weather_records: List[Dict]) -> List[Dict]:
        """
        Detect anomalies in weather data
        
        Checks for:
        - Extreme temperatures
        - Unrealistic precipitation
        - Physical inconsistencies
        """
        anomalies = []
        
        for idx, record in enumerate(weather_records):
            # Extreme temps (Peru coffee regions: typically 10-30C)
            temp_max = record.get("temp_max_c")
            temp_min = record.get("temp_min_c")
            
            if temp_max and temp_max > 50:
                anomalies.append({
                    "type": "extreme_high_temp",
                    "index": idx,
                    "temp_c": temp_max
                })
            
            if temp_min and temp_min < -20:
                anomalies.append({
                    "type": "extreme_low_temp",
                    "index": idx,
                    "temp_c": temp_min
                })
            
            # Temp inversion
            if temp_min and temp_max and temp_min > temp_max:
                anomalies.append({
                    "type": "temp_inversion",
                    "index": idx,
                    "temp_min": temp_min,
                    "temp_max": temp_max
                })
            
            # Excessive precipitation (>200mm/day is rare)
            precip = record.get("precipitation_mm")
            if precip and precip > 200:
                anomalies.append({
                    "type": "extreme_precipitation",
                    "index": idx,
                    "precip_mm": precip
                })
        
        return anomalies


class QualityReport:
    """Generate comprehensive quality report"""
    
    @staticmethod
    def generate_report(records: List[Dict], data_type: str) -> Dict:
        """
        Generate full quality report
        
        Args:
            records: List of data records
            data_type: "price", "freight", "weather"
        """
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "data_type": data_type,
            "total_records": len(records),
            "quality_score": 0.0,
            "issues": [],
            "recommendations": []
        }
        
        if not records:
            report["quality_score"] = 0.0
            report["issues"].append("No records to validate")
            return report
        
        # Detect anomalies
        if data_type == "price":
            anomalies = AnomalyDetector.detect_price_anomalies(records)
        elif data_type == "freight":
            anomalies = AnomalyDetector.detect_shipping_anomalies(records)
        elif data_type == "weather":
            anomalies = AnomalyDetector.detect_weather_anomalies(records)
        else:
            anomalies = []
        
        if anomalies:
            report["anomalies_detected"] = len(anomalies)
            report["issues"].append(f"Found {len(anomalies)} anomalies")
            
            if len(anomalies) > len(records) * 0.1:  # >10% anomalies
                report["recommendations"].append("Review data collection process - high anomaly rate")
        
        # Calculate quality score (0-1)
        quality_score = 1.0
        if len(anomalies) > 0:
            quality_score -= min(len(anomalies) / len(records), 0.3)
        
        report["quality_score"] = quality_score
        report["quality_label"] = "excellent" if quality_score > 0.9 else "good" if quality_score > 0.75 else "fair" if quality_score > 0.5 else "poor"
        
        return report
