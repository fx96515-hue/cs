# Quick Start: Peru Sourcing Intelligence

## Overview
Get started with the Peru Sourcing Intelligence System in 5 minutes.

## Prerequisites
- Running CoffeeStudio backend (FastAPI)
- PostgreSQL database
- Admin or Analyst user credentials

## Step 1: Run Database Migration

```bash
cd apps/api
alembic upgrade head
```

This creates:
- `regions` table with 20+ fields
- 7 new JSONB fields on `cooperatives` table

## Step 2: Seed Peru Regions

### Using API
```bash
curl -X POST http://localhost:8000/peru/regions/seed \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Expected Response
```json
{
  "status": "success",
  "created": 6,
  "updated": 0,
  "total_regions": 6,
  "regions": [
    "Cajamarca",
    "Junín",
    "San Martín",
    "Cusco",
    "Amazonas",
    "Puno"
  ]
}
```

## Step 3: Add Cooperative Data

### Example: Complete Cooperative Profile

```python
# Using Python API client or direct database insert
cooperative_data = {
    "name": "Cooperativa Norte",
    "region": "Cajamarca",
    "quality_score": 82,
    "operational_data": {
        "annual_volume_kg": 120000,
        "farmer_count": 550,
        "storage_capacity_kg": 180000,
        "processing_facilities": ["wet_mill", "dry_mill"],
        "years_exporting": 8
    },
    "export_readiness": {
        "has_export_license": True,
        "license_expiry_date": "2026-06-30",
        "senasa_registered": True,
        "certifications": ["Organic", "Fair Trade", "Rainforest Alliance"],
        "customs_issues_count": 0,
        "has_document_coordinator": True
    },
    "financial_data": {
        "annual_revenue_usd": 650000,
        "export_volume_kg": 100000,
        "fob_price_per_kg": 4.75
    },
    "communication_metrics": {
        "avg_response_hours": 20,
        "languages": ["Spanish", "English"],
        "missed_meetings": 0
    },
    "digital_footprint": {
        "has_website": True,
        "has_facebook": True,
        "has_instagram": True,
        "has_whatsapp": True,
        "has_photos": True,
        "has_cupping_scores": True
    }
}
```

### Using API
```bash
curl -X POST http://localhost:8000/cooperatives \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d @cooperative_data.json
```

## Step 4: Analyze Cooperative

```bash
curl -X POST http://localhost:8000/peru/cooperatives/1/analyze \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force_refresh": true}'
```

### Expected Response
```json
{
  "cooperative_id": 1,
  "cooperative_name": "Cooperativa Norte",
  "region": "Cajamarca",
  "analyzed_at": "2025-12-30T16:45:00Z",
  "supply_capacity": {
    "score": 95.0,
    "assessment": "strong",
    "breakdown": {
      "volume": {"score": 30, "volume_kg": 120000},
      "farmers": {"score": 20, "count": 550},
      "storage": {"score": 17, "capacity_kg": 180000},
      "facilities": {"score": 15, "types": ["wet_mill", "dry_mill"]},
      "experience": {"score": 12, "years": 8}
    }
  },
  "export_readiness": {
    "score": 100.0,
    "assessment": "ready"
  },
  "communication_quality": {
    "score": 88.0,
    "assessment": "excellent"
  },
  "price_benchmark": {
    "competitiveness_score": 95.88,
    "coop_price": 4.75,
    "benchmark_price": 4.85,
    "assessment": "competitive"
  },
  "risk_assessment": {
    "total_risk_score": 22.0,
    "assessment": "low"
  },
  "scores": {
    "supply_capacity": 95.0,
    "quality": 82.0,
    "export_readiness": 100.0,
    "price_competitiveness": 95.88,
    "communication": 88.0,
    "total": 90.63
  },
  "recommendation": {
    "level": "HIGHLY RECOMMENDED",
    "reasoning": "Excellent overall score with low risk profile. Strong candidate for sourcing.",
    "total_score": 90.63,
    "risk_score": 22.0
  }
}
```

## Step 5: Get Region Intelligence

```bash
curl http://localhost:8000/peru/regions/Cajamarca/intelligence \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Expected Response
```json
{
  "name": "Cajamarca",
  "country": "Peru",
  "description": "Northern Peru's largest coffee producing region...",
  "elevation_range": {
    "min_m": 1200,
    "max_m": 2100
  },
  "climate": {
    "avg_temperature_c": 19.5,
    "rainfall_mm": 1800,
    "humidity_pct": 75
  },
  "production": {
    "volume_kg": 75000000,
    "share_pct": 30.0,
    "harvest_months": "April-September"
  },
  "quality": {
    "typical_varieties": "Bourbon, Caturra, Typica, Catimor",
    "typical_processing": "Washed (primary), Honey, Natural",
    "profile": "Clean, sweet, balanced acidity, notes of chocolate...",
    "consistency_score": 84.0
  },
  "logistics": {
    "main_port": "Callao",
    "transport_time_hours": 14.0,
    "cost_per_kg": 0.32,
    "infrastructure_score": 84.0
  },
  "risks": {
    "weather": "medium",
    "political": "low",
    "logistics": "low"
  },
  "scores": {
    "growing_conditions": 82.5,
    "infrastructure": 84.0,
    "quality_consistency": 84.0
  }
}
```

## Common API Flows

### 1. List All Regions
```bash
GET /peru/regions
```

### 2. Get Cached Analysis
```bash
GET /peru/cooperatives/{id}/sourcing-analysis
```

### 3. Force Fresh Analysis
```bash
POST /peru/cooperatives/{id}/analyze
Body: {"force_refresh": true}
```

### 4. Refresh External Data
```bash
POST /peru/regions/refresh
Body: {"region_name": "Junín"}
```

## Interpretation Guide

### Score Ranges
- **90-100**: Excellent - Top tier supplier
- **80-89**: Very Good - Strong sourcing candidate
- **70-79**: Good - Suitable for sourcing
- **60-69**: Fair - Consider with caution
- **Below 60**: Poor - Not recommended

### Risk Ranges (lower is better)
- **0-29**: Low Risk - Safe to proceed
- **30-49**: Moderate Risk - Manageable with monitoring
- **50-59**: High Risk - Requires mitigation strategies
- **60+**: Very High Risk - Not recommended

### Recommendation Levels
1. **HIGHLY RECOMMENDED**: Best candidates (score ≥80, risk <30)
2. **RECOMMENDED**: Good candidates (score ≥70, risk <40)
3. **CONSIDER WITH CAUTION**: Requires evaluation (score ≥60, risk <50)
4. **MONITOR CLOSELY**: Needs improvement
5. **NOT RECOMMENDED**: Not suitable (score <60 or risk ≥60)

## Troubleshooting

### No Regions Found
```bash
# Run seed endpoint
POST /peru/regions/seed
```

### Cooperative Not Found
```bash
# Verify ID exists
GET /cooperatives/{id}
```

### Analysis Returns Low Scores
Check missing data:
- `operational_data`: Required for supply capacity
- `export_readiness`: Required for export score
- `financial_data`: Required for pricing
- `communication_metrics`: Required for communication score
- `quality_score`: Should be set (defaults to 50)

### Missing Pricing Benchmark
System uses ICO fallback (4.85 USD/kg) when no regional data available.

## Data Requirements

### Minimum Required Fields
For basic analysis:
- `name`, `region`
- `quality_score`

### Recommended Fields
For comprehensive analysis:
- All JSONB fields populated
- Recent data (within 6 months)

### Complete Profile
For HIGHLY RECOMMENDED rating:
- All operational data complete
- Full export readiness documentation
- Financial data with competitive pricing
- Good communication metrics
- Strong digital presence

## Example Python Usage

```python
import httpx

# Setup
BASE_URL = "http://localhost:8000"
TOKEN = "your_jwt_token"
headers = {"Authorization": f"Bearer {TOKEN}"}

# Seed regions
response = httpx.post(f"{BASE_URL}/peru/regions/seed", headers=headers)
print(response.json())

# Analyze cooperative
response = httpx.post(
    f"{BASE_URL}/peru/cooperatives/1/analyze",
    json={"force_refresh": True},
    headers=headers
)
analysis = response.json()

# Check recommendation
if analysis["recommendation"]["level"] == "HIGHLY RECOMMENDED":
    print(f"Strong candidate: {analysis['cooperative_name']}")
    print(f"Score: {analysis['scores']['total']}")
    print(f"Risk: {analysis['risk_assessment']['total_risk_score']}")
```

## Next Steps

1. **Explore Regions**: Review all 6 Peru regions intelligence
2. **Import Cooperatives**: Add your cooperative database
3. **Analyze All**: Run analysis on all cooperatives
4. **Filter Top Candidates**: Find HIGHLY RECOMMENDED cooperatives
5. **Monitor Scores**: Set up alerts for score changes
6. **Compare Regions**: Identify best sourcing regions

## Support

- **API Documentation**: `/docs` (Swagger UI)
- **Source Code**: `apps/api/app/services/cooperative_sourcing_analyzer.py`
- **Test Examples**: `apps/api/tests/test_peru_sourcing_api.py`

## Tips

1. Run analysis weekly to keep scores current
2. Use cached results for quick lookups
3. Force refresh when cooperative data changes
4. Compare cooperatives within same region
5. Track risk scores over time
6. Document reasoning for selections
