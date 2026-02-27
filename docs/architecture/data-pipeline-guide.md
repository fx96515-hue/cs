# Data Pipeline Implementation Summary

## Overview

This implementation provides an enterprise-grade data pipeline that fixes all data fetching issues in the CoffeeStudio platform. The pipeline includes multi-source providers with automatic fallback, circuit breaker protection, freshness monitoring, and comprehensive API endpoints.

## Key Features

### 1. Multi-Source Data Providers

#### Coffee Prices – Daily batch (`app.providers.coffee_prices`)
- **Primary**: Yahoo Finance (KC=F ICE Coffee C Futures)
- **Fallback 1**: Stooq (existing provider)
- **Fallback 2**: ICO static benchmark (always available)

**Usage:**
```python
from app.providers.coffee_prices import fetch_coffee_price

quote = fetch_coffee_price(use_fallback=True)
if quote:
    print(f"Coffee: ${quote.price_usd_per_lb}/lb from {quote.source_name}")
```

#### Coffee Prices – Realtime feed (`app.providers.ice_realtime`)

Enabled via the `REALTIME_PRICE_FEED_ENABLED=true` feature flag.

- **Primary**: Twelve Data REST API (`KC1!` symbol – ICE Coffee C front-month futures)
- **Fallback**: Yahoo Finance (KC=F)

**Usage:**
```python
from app.providers.ice_realtime import fetch_realtime_coffee_price

quote = fetch_realtime_coffee_price(api_key="<TWELVE_DATA_API_KEY>")
if quote:
    print(f"Realtime: ${quote.price_usd_per_lb}/lb from {quote.source_name}")
```

#### Redis Price Stream (`app.services.price_stream`)

Publishes every price fetch to a Redis Pub/Sub channel so WebSocket clients
receive push updates without polling the upstream API.

- **Cache key**: `coffee:price:latest`  (TTL = 120 s)
- **Pub/Sub channel**: `coffee:price:stream`

```python
from app.services.price_stream import fetch_and_publish, get_cached_price

# Push latest price to Redis (called by Celery beat task)
fetch_and_publish(redis_client, api_key=settings.TWELVE_DATA_API_KEY)

# Read cached price (used by the REST status endpoint and WebSocket on-connect)
price = get_cached_price(redis_client)
```

#### FX Rates (`app.providers.fx_rates`)
- **Primary**: ECB (European Central Bank)
- **Fallback 1**: ExchangeRate-API (free tier)
- **Fallback 2**: Frankfurter API

**Usage:**
```python
from app.providers.fx_rates import fetch_fx_rate

rate = fetch_fx_rate("USD", "EUR")
if rate:
    print(f"FX: 1 {rate.base} = {rate.rate} {rate.quote}")
```

#### Peru Intelligence (`app.providers.peru_intel`)
- **Weather**: OpenMeteo API (free, no key required)
- **Production**: Perplexity Sonar API (requires API key)

**Usage:**
```python
from app.providers.peru_intel import fetch_openmeteo_weather

weather = fetch_openmeteo_weather("Cajamarca")
if weather:
    print(f"Temperature: {weather.current_temp_c}°C")
```

### 2. Data Pipeline Orchestrator

The orchestrator coordinates all data collection with proper sequencing, error handling, and circuit breaker integration.

**Usage:**
```python
from app.services.data_pipeline.orchestrator import DataPipelineOrchestrator

orchestrator = DataPipelineOrchestrator(db, redis_client)

# Run market pipeline (FX + coffee prices)
result = orchestrator.run_market_pipeline()

# Run intelligence pipeline (Peru weather + news)
result = orchestrator.run_intelligence_pipeline()

# Run full pipeline
result = orchestrator.run_full_pipeline()
```

### 3. Circuit Breaker

Redis-backed circuit breaker prevents cascading failures when external sources are down.

**States:**
- **CLOSED**: Normal operation, requests allowed
- **OPEN**: Too many failures, requests blocked for cooldown period
- **HALF_OPEN**: Testing recovery, limited requests allowed

**Configuration (in .env):**
```bash
DATA_PIPELINE_CIRCUIT_BREAKER_THRESHOLD=3  # Failures before opening
DATA_PIPELINE_CIRCUIT_BREAKER_TIMEOUT_S=300  # Cooldown period (5 min)
```

### 4. Freshness Monitoring

Track data staleness across all sources.

**Usage:**
```python
from app.services.data_pipeline.freshness import DataFreshnessMonitor

monitor = DataFreshnessMonitor(db)
report = monitor.get_freshness_report()

print(f"Overall status: {report['overall_status']}")
for category, status in report['categories'].items():
    print(f"{category}: {'stale' if status['stale'] else 'fresh'}")
```

## API Endpoints

All endpoints require authentication (admin or analyst role).

### GET `/data-health/status`
Returns comprehensive freshness status for all data sources.

**Response:**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "overall_status": "healthy",
  "categories": {
    "fx_rates": {
      "USD_EUR": {
        "last_updated": "2024-01-15T07:30:00Z",
        "age_hours": 3.0,
        "stale": false,
        "status": "fresh"
      }
    },
    "coffee_prices": { ... },
    "weather": { ... }
  }
}
```

### GET `/data-health/sources`
Lists all data sources and their circuit breaker status.

**Response:**
```json
{
  "sources": {
    "fx_rates": {
      "provider": "fx_rates",
      "state": "closed",
      "failures": 0,
      "failure_threshold": 3
    },
    "coffee_prices": { ... }
  }
}
```

### POST `/data-health/refresh-all`
Triggers complete data pipeline refresh (synchronous).

**Response:**
```json
{
  "status": "success",
  "duration_seconds": 12.5,
  "operations": {
    "market": { "status": "success", ... },
    "intelligence": { "status": "success", ... }
  },
  "errors": []
}
```

### POST `/data-health/refresh-market`
Triggers market data refresh only (FX + coffee prices).

### POST `/data-health/refresh-intelligence`
Triggers intelligence pipeline (Peru weather + news).

### POST `/data-health/reset-circuit/{provider}`
Manually reset a circuit breaker (admin only).

## Celery Tasks

### `refresh_market`
Enhanced market refresh with multi-source fallback.
- Runs via orchestrator
- Updates FX rates and coffee prices
- Recomputes cooperative scores
- Generates daily report

**Schedule:** Configured via `MARKET_REFRESH_TIMES` (default: 07:30, 14:00, 20:00)

### `refresh_intelligence`
Refreshes Peru intelligence pipeline.
- Updates weather data for all regions
- Refreshes news
- Uses circuit breaker protection

**Schedule:** Configured via `INTELLIGENCE_REFRESH_TIMES` (default: every 6 hours)

### `auto_enrich_stale`
Auto-enriches entities that haven't been updated recently.
- Finds top 10 stalest cooperatives and roasters
- Enriches them with latest data
- Uses staleness thresholds from config

**Schedule:** Configured via `AUTO_ENRICH_TIME` (default: 03:00 daily)

## Configuration

Add to `.env`:

```bash
# Data Pipeline settings
DATA_PIPELINE_CIRCUIT_BREAKER_THRESHOLD=3
DATA_PIPELINE_CIRCUIT_BREAKER_TIMEOUT_S=300
DATA_PIPELINE_MAX_RETRIES=3

# Intelligence refresh schedule (HH:MM,HH:MM,...)
INTELLIGENCE_REFRESH_TIMES=06:00,12:00,18:00,00:00
AUTO_ENRICH_TIME=03:00

# Perplexity API (optional, for Peru production intelligence)
PERPLEXITY_API_KEY=your_api_key_here
```

## Updated Existing Services

### `peru_data_sources.py`
All stub functions now return real data:
- `fetch_jnc_data()`: Uses Perplexity to research JNC production data
- `fetch_minagri_data()`: Uses Perplexity for agricultural statistics
- `fetch_senamhi_weather()`: Uses OpenMeteo for weather (free, no key)
- `fetch_ico_price_data()`: Returns ICO fallback prices

### `peru_sourcing_intel.py`
`refresh_region_data()` now actually updates the Region model in the database with fresh weather data.

### `ml/data_collection.py`
Placeholder methods now implemented:
- `enrich_freight_data()`: Extracts freight data from completed shipments
- `enrich_price_data()`: Extracts price data from closed deals

## Testing

### Unit Tests
- `test_coffee_prices_provider.py`: Tests for coffee price fetching
- `test_fx_rates_provider.py`: Tests for FX rate fetching
- `test_circuit_breaker.py`: Tests for circuit breaker behavior

Run tests:
```bash
# In Docker
docker compose exec backend pytest apps/api/tests/test_coffee_prices_provider.py -v

# Or run all tests
docker compose exec backend pytest apps/api/tests/ -v
```

## Monitoring

### Check Data Health
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/data-health/status
```

### Check Circuit Breakers
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/data-health/sources
```

### Manual Refresh
```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/data-health/refresh-all
```

## Logging

All providers use structured logging (structlog). Look for:
- `coffee_price_fetch_success` / `coffee_price_fetch_failed`
- `fx_rate_fetch_success` / `fx_rate_all_sources_failed`
- `circuit_breaker_state_change`
- `market_pipeline_complete`
- `intelligence_pipeline_complete`

Example log output:
```json
{
  "event": "coffee_price_fetch_success",
  "source": "yahoo_finance",
  "price": 210.5,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Troubleshooting

### Circuit breaker stuck open?
Reset it via API:
```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/data-health/reset-circuit/coffee_prices
```

### Data not updating?
1. Check circuit breaker status
2. Review logs for errors
3. Verify API keys (Perplexity) if needed
4. Manually trigger refresh via API

### Weather data not available?
OpenMeteo has rate limits. If you hit them:
1. Circuit breaker will open automatically
2. Wait for cooldown (5 minutes default)
3. Data will resume after cooldown

## Benefits

1. **Resilience**: Multiple sources with automatic fallback
2. **Reliability**: Circuit breakers prevent cascading failures
3. **Visibility**: Freshness monitoring and health endpoints
4. **Automation**: Scheduled tasks keep data current
5. **Real Data**: All stubs replaced with actual implementations
6. **Free Tier**: Most providers use free APIs (OpenMeteo, Frankfurter, ExchangeRate-API)

## Next Steps

1. Monitor data health dashboard in production
2. Adjust circuit breaker thresholds based on observed patterns
3. Add more data sources as needed
4. Consider caching frequently accessed data in Redis
5. Set up alerts for prolonged circuit breaker OPEN states
