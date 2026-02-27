# Peru Sourcing Intelligence System

## Overview

The Peru Sourcing Intelligence System is a comprehensive buyer-side evaluation framework for assessing Peru coffee cooperatives. It provides data-driven scoring algorithms, regional intelligence, and sourcing recommendations to support informed purchasing decisions.

## Key Features

### 1. Regional Intelligence
- **6 Major Peru Regions**: Cajamarca, Junín, San Martín, Cusco, Amazonas, Puno
- **Growing Conditions Analysis**: Elevation, climate, soil quality scoring
- **Production Data**: Volume, market share, harvest seasons
- **Quality Profiles**: Typical varieties, processing methods, flavor profiles
- **Logistics Intelligence**: Port access, transport times, costs
- **Risk Assessment**: Weather, political, logistics risks

### 2. Cooperative Evaluation
Multi-dimensional scoring across 5 key areas:

#### Supply Capacity (30% weight)
- **Volume**: 30 points (≥100k kg = 30, ≥50k = 25, ≥25k = 20, ≥10k = 15, else 5)
- **Farmer Count**: 20 points (≥500 = 20, ≥200 = 17, ≥100 = 14, ≥50 = 10, else 5)
- **Storage**: 20 points (≥200k kg = 20, ≥100k = 17, ≥50k = 14, ≥25k = 10, else 5)
- **Processing**: 15 points (wet mill +8, dry mill +7)
- **Experience**: 15 points (≥10y = 15, ≥5y = 12, ≥3y = 9, ≥1y = 6, else 2)

#### Quality Score (25% weight)
Uses existing cooperative quality_score field

#### Export Readiness (20% weight)
- **License**: 25 points (valid export license with expiry)
- **SENASA**: 25 points (registered with Peru agricultural authority)
- **Certifications**: 25 points (3+ = 25, 2 = 20, 1 = 15, else 5)
- **Customs**: 15 points (0 issues = 15, ≤2 = 10, ≤5 = 5, else 0)
- **Coordinator**: 10 points (has document coordinator)

#### Price Competitiveness (15% weight)
- **Calculation**: 100 - (abs(price_diff_pct) * 2)
- **Benchmark**: Regional or ICO fallback (4.85 USD/kg FOB)
- **Assessment**: competitive (≥70), market_rate (≥50), expensive (<50)

#### Communication Quality (10% weight)
- **Response Time**: 25 points (≤24h = 25, ≤48h = 20, ≤72h = 10, else 5)
- **Languages**: 25 points (English +15, German +10, base Spanish 5)
- **Digital Presence**: 20 points (website +8, Facebook +4, Instagram +4, WhatsApp +4)
- **Documentation**: 15 points (photos +8, cupping scores +7)
- **Meetings**: 15 points (0 missed = 15, ≤1 = 12, ≤3 = 8, else 3)

### 3. Risk Assessment
Comprehensive risk scoring (0-100, lower is better):

- **Financial Risk** (max 25): Based on annual revenue
- **Quality Risk** (max 20): Inverse of quality score
- **Delivery Risk** (max 25): Export experience + customs issues
- **Geographic Risk** (max 15): Altitude and logistics challenges
- **Communication Risk** (max 15): Response time + missed meetings

### 4. Recommendation Engine
Automated recommendations based on total score and risk:

- **HIGHLY RECOMMENDED**: score ≥80 AND risk <30
- **RECOMMENDED**: score ≥70 AND risk <40
- **CONSIDER WITH CAUTION**: score ≥60 AND risk <50
- **MONITOR CLOSELY**: moderate scores
- **NOT RECOMMENDED**: score <60 OR risk ≥60

## API Endpoints

### Region Intelligence

#### List All Regions
```
GET /peru/regions
```
Returns list of Peru regions with basic information.

#### Get Region Intelligence
```
GET /peru/regions/{region_name}/intelligence
```
Returns comprehensive region data including scores, production, logistics, and risks.

#### Seed Regions
```
POST /peru/regions/seed
```
Seeds database with 6 major Peru regions. Admin only.

#### Refresh Region Data
```
POST /peru/regions/refresh
Body: {"region_name": "Cajamarca"}
```
Refreshes region data from external sources (currently stubs).

### Cooperative Analysis

#### Get Sourcing Analysis (Cached)
```
GET /peru/cooperatives/{coop_id}/sourcing-analysis
```
Returns cached analysis if available.

#### Analyze Cooperative (Fresh)
```
POST /peru/cooperatives/{coop_id}/analyze
Body: {"force_refresh": true}
```
Performs fresh analysis, updates cache.

## Region Profiles

### Cajamarca (30% production)
- **Elevation**: 1200-2100m
- **Score**: 84
- **Strengths**: Largest producer, strong infrastructure, consistent quality
- **Logistics**: 14h to Callao, $0.32/kg
- **Profile**: Clean, sweet, balanced acidity, chocolate, caramel, citrus

### Junín (20% production)
- **Elevation**: 1200-1800m
- **Score**: 83
- **Strengths**: Best logistics (8h), excellent infrastructure (88)
- **Logistics**: 8h to Callao, $0.28/kg
- **Profile**: Bright acidity, fruity, floral undertones

### San Martín (18% production)
- **Elevation**: 900-1700m
- **Score**: 81
- **Challenges**: High humidity (85%), drying challenges
- **Logistics**: 18h to Callao, $0.38/kg
- **Profile**: Full body, nutty, chocolate, variable quality

### Cusco (15% production)
- **Elevation**: 1400-2200m
- **Score**: 86
- **Strengths**: High quality, complex profiles
- **Challenges**: Mountain logistics, longer transport (24h)
- **Profile**: Complex, bright, floral, fruity, wine-like

### Amazonas (8% production)
- **Elevation**: 1200-2100m
- **Score**: 85
- **Strengths**: Clean, bright, high-quality micro-lots
- **Logistics**: 20h to Callao, $0.40/kg
- **Profile**: Clean acidity, citrus, stone fruit, floral

### Puno (5% production)
- **Elevation**: 1500-2300m (highest)
- **Score**: 87
- **Strengths**: Distinctive floral profiles, very high altitude
- **Challenges**: Longest distance (26h), highest cost ($0.45/kg)
- **Profile**: Sweet, floral, delicate, complex

## Data Structure

### Cooperative JSONB Fields

```python
operational_data = {
    "annual_volume_kg": int,
    "farmer_count": int,
    "storage_capacity_kg": int,
    "processing_facilities": ["wet_mill", "dry_mill"],
    "years_exporting": int
}

export_readiness = {
    "has_export_license": bool,
    "license_expiry_date": "YYYY-MM-DD",
    "senasa_registered": bool,
    "certifications": ["Organic", "Fair Trade"],
    "customs_issues_count": int,
    "has_document_coordinator": bool
}

financial_data = {
    "annual_revenue_usd": float,
    "export_volume_kg": float,
    "fob_price_per_kg": float
}

communication_metrics = {
    "avg_response_hours": float,
    "languages": ["Spanish", "English", "German"],
    "missed_meetings": int
}

digital_footprint = {
    "has_website": bool,
    "has_facebook": bool,
    "has_instagram": bool,
    "has_whatsapp": bool,
    "has_photos": bool,
    "has_cupping_scores": bool
}

sourcing_scores = {
    # Cached analysis results
    "analyzed_at": "ISO timestamp",
    "supply_capacity": {...},
    "export_readiness": {...},
    "scores": {...},
    "recommendation": {...}
}
```

## External Data Sources (Stubs)

Current version includes stub functions for future integration:

- **JNC** (Junta Nacional del Café): Production volumes, quality reports
- **MINAGRI** (Ministry of Agriculture): Statistics, certifications, programs
- **SENAMHI**: Weather data, forecasts, climate history
- **ICO** (International Coffee Organization): Price data, market reports

## Usage Notes

1. **Caching**: Analysis results are cached in `sourcing_scores` field
2. **Permissions**: Most endpoints require analyst/admin role
3. **Missing Data**: System handles missing data gracefully with neutral scores
4. **Buyer Focus**: System is designed for German buyer evaluating Peru suppliers
5. **FOB Pricing**: All prices in USD per kg, FOB (Free On Board) basis
