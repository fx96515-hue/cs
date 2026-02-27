# Changelog — CoffeeStudio OptionD

## v0.4.0-ml — ML Predictive Models (Freight & Pricing)

### Added
- **ML Models for Predictive Analytics**:
  - Freight cost prediction using Random Forest ML models
  - Coffee price forecasting and trend analysis
  - Transit time predictions for shipping routes
  - Optimal purchase timing recommendations
  
- **New Database Tables**:
  - `freight_history` - Historical freight shipment data for training
  - `coffee_price_history` - Historical coffee price data
  - `ml_models` - ML model metadata and performance tracking
  
- **ML API Endpoints** (`/api/v1/ml/`):
  - `POST /predict-freight` - Predict freight costs
  - `POST /predict-transit-time` - Predict shipping transit time
  - `GET /freight-cost-trend` - Get historical cost trends
  - `POST /predict-coffee-price` - Predict coffee prices
  - `POST /forecast-price-trend` - Forecast price trends
  - `POST /optimal-purchase-timing` - Get purchase recommendations
  - `GET /models` - List ML models
  - `GET /models/{id}` - Get model details
  - `POST /models/{id}/retrain` - Trigger model retraining
  - `POST /data/import-freight` - Import freight training data
  - `POST /data/import-prices` - Import price training data

- **ML Services**:
  - `FreightPredictionService` - Freight cost and transit predictions
  - `CoffeePricePredictionService` - Coffee price predictions
  - `MLModelManagementService` - Model lifecycle management
  - `DataCollectionService` - Training data import

- **ML Core Models**:
  - `FreightCostModel` - Random Forest model for freight predictions
  - `CoffeePriceModel` - Random Forest model for price predictions
  - Feature engineering with one-hot encoding and normalization
  - Confidence interval calculation using tree ensemble variance

- **Sample Data**:
  - 80 historical freight records (5 routes, 18 months)
  - 150 historical coffee price records (Peru, Colombia)
  - 2 pre-configured ML model metadata records

### Dependencies Added
- `scikit-learn>=1.3.0` - Machine learning models
- `pandas>=2.0.0` - Data manipulation
- `numpy>=1.24.0` - Numerical operations
- `joblib>=1.3.0` - Model persistence

### Technical Details
- All predictions include confidence scores and intervals
- Models use Random Forest for explainability
- Graceful degradation when data is sparse
- Type-safe with MyPy strict mode
- Async-compatible service layer
- Comprehensive API schemas with Pydantic

### Documentation
- `apps/api/ML_MODELS_DOCUMENTATION.md` - Complete ML feature documentation
- Inline documentation in all ML modules
- Usage examples for all endpoints

## v0.3.0-data — Data Backbone (News/Regions/Enrich/Dedup/Logistics/Outreach)

### Added
- New DB tables: `news_items`, `peru_regions`, `web_extracts`, `entity_aliases`, `entity_events`.
- Data APIs:
  - `GET/POST /news` (refresh + list)
  - `GET/POST /regions/peru` (seed + list)
  - `POST /enrich/{entity_type}/{id}` (web fetch + optional LLM extraction)
  - `GET /dedup/suggest` (duplicate suggestions)
  - `POST /logistics/landed-cost` (landed cost calculator)
  - `POST /outreach/generate` (email drafts)
  - `GET/POST /kb` (editable logistics/customs KB docs)
  - `GET/POST /cuppings` (SCA-style cupping results)
- Celery beat schedule extended: `refresh_news` uses `NEWS_REFRESH_TIMES`.

### Changed
- `.env.example` extended with freshness defaults + refresh times.
- `README_WINDOWS.md` extended with optional Data-Gates A-E.

### Notes
- Perplexity-backed features stay optional; without `PERPLEXITY_API_KEY` the app runs and news/enrich LLM parts return `skipped`.

## v0.2.1c — Auth/Bootstrap Fix (pbkdf2) + Windows-first env

### Fixed
- Eliminated `/auth/dev/bootstrap` 500 caused by `passlib`/`bcrypt` backend incompatibility (bcrypt 4.x API change).
- Frontend default login email is now a valid email (`admin@coffeestudio.com`).

### Changed
- Password hashing switched to `pbkdf2_sha256` (stable, no native bcrypt bindings).
- `docker-compose.yml` now uses `env_file: ./.env` for consistent environment handling.
- Backend starts with `alembic upgrade head` before `uvicorn` to ensure migrations are always applied.
- Added backend healthcheck (Compose service_healthy gating for apps/web/worker/beat).

### Added
- `README_WINDOWS.md` with explicit Gates 0-9.

### Security
- `.env.example` contains no real secrets; local `run_windows.ps1` generates JWT secret and sets dev bootstrap password in the local `.env`.

## 0.3.2-maxstack (2025-12-23)
- MAX stack: Traefik single-entrypoint, Portainer, Grafana+Prometheus+Loki+Tempo, Blackbox, cAdvisor, node-exporter.
- MAX automation: n8n workflows, Keycloak (dev), LLM stack (Ollama + Open WebUI + LiteLLM), Langfuse observability.
- Ops: WUD update dashboard + optional Watchtower.
- Windows: stepwise runner with automatic backups + diagnostics + guided troubleshooting.
