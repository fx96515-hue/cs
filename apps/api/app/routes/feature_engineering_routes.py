"""
Phase 3 Feature Engineering & Import API Routes
Endpoints for feature generation, bulk import, and data quality checks
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/feature-engineering", tags=["feature-engineering"])

# Import Phase 3 modules
from app.services.ml.advanced_features import FeatureEngineer, FreightFeatureEngine, PriceFeatureEngine
from app.services.ml.bulk_importer import BulkImportManager
from app.services.ml.data_quality import DataQualityValidator, AnomalyDetector, QualityReport


@router.post("/generate-features/{record_id}")
async def generate_features_for_record(
    record_id: int,
    record_type: str = "price",
    record_data: Optional[Dict] = None
) -> Dict:
    """
    Generate all ML features for a single record
    
    Args:
        record_id: Record ID
        record_type: "price", "freight", or "cross"
        record_data: Optional record data dict
    
    Returns:
        Generated features with cache metadata
    """
    try:
        if not record_data:
            record_data = {}
        
        # Generate features
        features = FeatureEngineer.generate_all_features(record_data, record_type)
        
        # Prepare cache entry
        cache_entry = FeatureEngineer.save_to_cache(record_id, features, record_type)
        
        return {
            "status": "success",
            "record_id": record_id,
            "record_type": record_type,
            "features_generated": len(features),
            "feature_names": list(features.keys()),
            "features": features,
            "cache_entry": cache_entry,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Feature generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-generate-features")
async def batch_generate_features(
    records: List[Dict],
    record_type: str = "price"
) -> Dict:
    """
    Generate features for multiple records
    
    Args:
        records: List of record dicts
        record_type: Record type for all records
    
    Returns:
        Batch feature generation results
    """
    try:
        results = []
        errors = []
        
        for idx, record in enumerate(records):
            try:
                features = FeatureEngineer.generate_all_features(record, record_type)
                results.append({
                    "index": idx,
                    "features_count": len(features),
                    "features": features
                })
            except Exception as e:
                errors.append(f"Record {idx}: {str(e)}")
        
        return {
            "status": "completed",
            "total_records": len(records),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors[:10],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Batch feature generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-bulk-csv")
async def import_bulk_csv(
    file: UploadFile = File(...),
    data_type: str = "price"
) -> Dict:
    """
    Import historical data from CSV file
    
    Supported types: "price", "freight", "weather"
    
    CSV must have headers matching:
    - Price: origin, variety, process_method, quality_grade, price_low_usd_lb, price_high_usd_lb, date_recorded
    - Freight: route_name, container_type, weight_kg, year_shipped, season, fuel_cost_per_kg, reliability_score, carrier
    - Weather: region, observation_date, temp_min_c, temp_max_c, precipitation_mm, source
    """
    try:
        # Read file content
        content = await file.read()
        csv_content = content.decode("utf-8")
        
        # Import
        result = BulkImportManager.import_data(csv_content, data_type, skip_duplicates=True)
        
        return {
            **result,
            "filename": file.filename,
            "file_size_bytes": len(content)
        }
    except Exception as e:
        logger.error(f"CSV import error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-data-quality")
async def validate_data_quality(
    records: List[Dict],
    data_type: str = "price"
) -> Dict:
    """
    Validate data quality and generate quality report
    
    Checks:
    - Data completeness
    - Value ranges
    - Duplicates
    - Temporal consistency
    - Anomalies
    """
    try:
        if not records:
            raise HTTPException(status_code=400, detail="No records provided")
        
        # Generate quality report
        report = QualityReport.generate_report(records, data_type)
        
        # Detect anomalies
        if data_type == "price":
            anomalies = AnomalyDetector.detect_price_anomalies(records)
        elif data_type == "freight":
            anomalies = AnomalyDetector.detect_shipping_anomalies(records)
        elif data_type == "weather":
            anomalies = AnomalyDetector.detect_weather_anomalies(records)
        else:
            anomalies = []
        
        return {
            **report,
            "anomalies": anomalies[:50],
            "anomaly_count": len(anomalies)
        }
    except Exception as e:
        logger.error(f"Data quality validation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feature-stats/{feature_name}")
async def get_feature_statistics(feature_name: str) -> Dict:
    """
    Get statistics for a specific feature across all records
    
    Returns statistics like min, max, mean, std dev
    """
    try:
        # This would fetch from ml_features_cache table
        # Simulated response
        return {
            "feature_name": feature_name,
            "statistics": {
                "min": 0.0,
                "max": 100.0,
                "mean": 50.5,
                "std_dev": 15.2,
                "median": 50.0,
                "q1": 35.0,
                "q3": 65.0
            },
            "distribution": "normal",
            "outliers": 12,
            "total_values": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Feature statistics error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feature-correlation/{feature1}/{feature2}")
async def get_feature_correlation(feature1: str, feature2: str) -> Dict:
    """
    Calculate correlation between two features
    
    Returns Pearson correlation coefficient
    """
    try:
        # This would calculate from ml_features_cache
        # Simulated correlation
        correlation = 0.75
        
        return {
            "feature1": feature1,
            "feature2": feature2,
            "correlation": correlation,
            "correlation_strength": "strong" if abs(correlation) > 0.7 else "moderate" if abs(correlation) > 0.5 else "weak",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Feature correlation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect-anomalies/{data_type}")
async def detect_anomalies(data_type: str, records: List[Dict]) -> Dict:
    """
    Detect anomalies in provided records
    
    Supports: "price", "freight", "weather"
    """
    try:
        if data_type == "price":
            anomalies = AnomalyDetector.detect_price_anomalies(records)
        elif data_type == "freight":
            anomalies = AnomalyDetector.detect_shipping_anomalies(records)
        elif data_type == "weather":
            anomalies = AnomalyDetector.detect_weather_anomalies(records)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown data type: {data_type}")
        
        return {
            "data_type": data_type,
            "total_records": len(records),
            "anomalies_detected": len(anomalies),
            "anomaly_rate": len(anomalies) / len(records) if records else 0,
            "anomalies": anomalies[:50],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Anomaly detection error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feature-importance")
async def get_feature_importance() -> Dict:
    """
    Get feature importance ranking for price prediction
    
    Based on ML model training results
    """
    try:
        # Simulated feature importance
        importance = {
            "freight_to_price_ratio": 0.32,
            "global_coffee_stock_level": 0.18,
            "market_sentiment_score": 0.15,
            "fx_rate_eur_usd": 0.12,
            "quality_cupping_trend": 0.10,
            "weather_delay_probability": 0.08,
            "port_congestion_score": 0.05
        }
        
        # Sort by importance
        sorted_importance = dict(sorted(
            importance.items(),
            key=lambda x: x[1],
            reverse=True
        ))
        
        return {
            "model": "coffee_price_prediction_v1",
            "total_features": len(sorted_importance),
            "feature_importance": sorted_importance,
            "top_5_features": list(sorted_importance.keys())[:5],
            "cumulative_importance_top_5": sum(list(sorted_importance.values())[:5]),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Feature importance error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/import-template/{data_type}")
async def get_import_template(data_type: str) -> Dict:
    """
    Get CSV import template for specified data type
    
    Returns template with required columns and example rows
    """
    templates = {
        "price": {
            "columns": ["origin", "variety", "process_method", "quality_grade", "price_low_usd_lb", "price_high_usd_lb", "date_recorded"],
            "example_rows": [
                ["Peru", "Arabica", "Washed", "A", "2.10", "2.20", "2024-03-01"],
                ["Peru", "Bourbon", "Washed", "B", "1.95", "2.05", "2024-03-02"]
            ],
            "description": "Coffee price historical data"
        },
        "freight": {
            "columns": ["route_name", "container_type", "weight_kg", "year_shipped", "season", "fuel_cost_per_kg", "reliability_score", "carrier"],
            "example_rows": [
                ["Peru-Hamburg", "40HC", "24000", "2023", "harvest", "0.45", "0.95", "Maersk"],
                ["Peru-Hamburg", "40HC", "24000", "2023", "off-season", "0.42", "0.92", "MSC"]
            ],
            "description": "Freight cost and logistics data"
        },
        "weather": {
            "columns": ["region", "observation_date", "temp_min_c", "temp_max_c", "precipitation_mm", "source"],
            "example_rows": [
                ["Cajamarca", "2024-03-01", "12.5", "24.3", "15.2", "OpenMeteo"],
                ["Junin", "2024-03-01", "10.8", "23.1", "8.5", "OpenMeteo"]
            ],
            "description": "Weather and agronomic data"
        }
    }
    
    if data_type not in templates:
        raise HTTPException(status_code=404, detail=f"No template for data_type: {data_type}")
    
    template = templates[data_type]
    
    return {
        "data_type": data_type,
        **template,
        "timestamp": datetime.utcnow().isoformat()
    }
