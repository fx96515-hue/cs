# ML Predictive Models Documentation

## Overview

This module provides machine learning-powered predictive analytics for coffee trading operations, specifically:

1. **Freight Cost Prediction** - Estimate shipping costs based on routes, weights, and historical data
2. **Coffee Price Forecasting** - Predict coffee prices based on origin, quality, and market conditions

Both prediction tasks support two algorithm backends, selectable via the `ML_MODEL_TYPE` environment variable:

| `ML_MODEL_TYPE` | Algorithm | Notes |
|---|---|---|
| `random_forest` (default) | scikit-learn RandomForestRegressor | Robust fallback, no extra dependencies |
| `xgboost` | XGBoost XGBRegressor ≥ 2.0 | Higher accuracy, feature importance (gain) |

## Features

### Freight Cost Prediction

The freight cost prediction system uses a Random Forest Regressor to predict shipping costs based on:

- **Route**: Origin-destination port pairs (e.g., "Callao-Hamburg")
- **Weight**: Shipment weight in kilograms
- **Container Type**: 20ft or 40ft containers
- **Season**: Quarter of the year (Q1-Q4)
- **Historical Patterns**: Average costs for similar shipments
- **Optional**: Fuel price index and port congestion scores

**Confidence Scores**: Each prediction includes a confidence interval and score based on the amount of historical data available.

**API Endpoints**:
- `POST /api/v1/ml/predict-freight` - Predict freight cost
- `POST /api/v1/ml/predict-transit-time` - Predict transit time
- `GET /api/v1/ml/freight-cost-trend` - Get historical cost trends

### Coffee Price Prediction

The coffee price prediction system forecasts prices based on:

- **Origin**: Country and region (e.g., Peru - Cajamarca)
- **Coffee Attributes**: Variety, processing method, quality grade
- **Quality Score**: Cupping score (0-100)
- **Certifications**: Organic, Fair Trade, etc.
- **Market Context**: ICE Coffee C futures price
- **Seasonality**: Time of year effects

**Features**:
- Price predictions with confidence intervals
- 6-12 month price trend forecasts
- Optimal purchase timing recommendations
- Market comparison analysis

**API Endpoints**:
- `POST /api/v1/ml/predict-coffee-price` - Predict coffee price
- `POST /api/v1/ml/forecast-price-trend` - Forecast future prices
- `POST /api/v1/ml/optimal-purchase-timing` - Get purchase recommendations

### Model Management

The system tracks ML model metadata including:
- Model version and training date
- **Algorithm** (`random_forest` or `xgboost`) – stored per model in the DB
- Performance metrics (MAE, RMSE, R² score)
- Feature sets used
- Training data counts
- Model status (active, training, deprecated)

**API Endpoints**:
- `GET /api/v1/ml/models` - List all models
- `GET /api/v1/ml/models/{id}` - Get model details (includes `algorithm`)
- `GET /api/v1/ml/models/{id}/feature-importance` - Get feature importances (XGBoost & RF)
- `POST /api/v1/ml/models/{id}/retrain` - Trigger retraining

### Data Collection

Historical data can be imported to improve model accuracy:

**API Endpoints**:
- `POST /api/v1/ml/data/import-freight` - Import freight records
- `POST /api/v1/ml/data/import-prices` - Import price records

## Architecture

### Models
- `FreightHistory` - Historical freight shipment records
- `CoffeePriceHistory` - Historical coffee price records
- `MLModel` - ML model metadata and performance tracking (includes `algorithm` column)

### ML Implementations
- `FreightCostModel` - Random Forest model for freight costs
- `CoffeePriceModel` - Random Forest model for coffee prices
- `XGBoostFreightCostModel` - XGBoost model for freight costs
- `XGBoostCoffeePriceModel` - XGBoost model for coffee prices
- `model_factory` - Factory functions `create_price_model()` / `create_freight_model()` controlled by `ML_MODEL_TYPE`

### Services
- `FreightPredictionService` - Freight cost and transit predictions
- `CoffeePricePredictionService` - Coffee price predictions and forecasts
- `MLModelManagementService` - Model lifecycle management
- `DataCollectionService` - Training data import and enrichment

## Algorithms

### Factory Pattern / Feature Flag

Set `ML_MODEL_TYPE` in your `.env` file to choose the algorithm:

```bash
# Default – Random Forest (no extra dependencies)
ML_MODEL_TYPE=random_forest

# XGBoost (requires xgboost>=2.0.0 and libgomp1 on Linux)
ML_MODEL_TYPE=xgboost
```

Both backends implement identical interfaces (`train` / `predict` /
`predict_with_confidence` / `save` / `load` / `get_feature_importance`).  
Existing Random Forest model files remain usable as a fallback; the
`algorithm` column in the `ml_models` DB table records which backend was
used to train each model.

### XGBoost Regressor (XGBRegressor)

When `ML_MODEL_TYPE=xgboost`:

- **n_estimators**: 300 trees
- **max_depth**: 6 levels
- **learning_rate**: 0.05
- **subsample / colsample_bytree**: 0.8 (reduces overfitting)
- **tree_method**: `hist` (fast histogram-based algorithm)
- **Feature Importance**: Returns gain-based importances normalised to sum 1

**Why XGBoost?**
- Typically 10–20 % lower MAE vs Random Forest on tabular data
- Regularisation prevents overfitting
- Native feature importance (gain)
- Fast training with histogram method

### Random Forest Regressor

Both prediction models use scikit-learn's Random Forest Regressor:

- **n_estimators**: 100 decision trees
- **max_depth**: 10 levels
- **Ensemble approach**: Reduces overfitting, provides confidence estimates

**Why Random Forest?**
- Handles mixed feature types (categorical and numerical)
- Robust to outliers
- Provides feature importance
- Explainable predictions
- Good performance with limited data

### Feature Engineering

**Freight Model**:
- One-hot encoding for routes, container types, carriers
- Weight normalization
- Seasonal encoding (Q1-Q4)
- Fuel price and congestion score handling

**Price Model**:
- Origin encoding (country + region)
- Variety and processing method encoding
- Quality grade encoding
- Cupping score normalization
- Certification count
- ICE C price normalization
- Month extraction for seasonality

### Confidence Intervals

Confidence intervals are calculated using the standard deviation of predictions across all trees in the Random Forest:

```
lower_bound = prediction - 1.96 * std
upper_bound = prediction + 1.96 * std
```

This provides a 95% confidence interval around each prediction.

### Confidence Scores

Confidence scores (0-1) are based on:
- Number of similar historical records
- Data recency
- Feature completeness

## Performance Metrics

Models are evaluated using:

- **MAE (Mean Absolute Error)**: Average absolute prediction error
- **RMSE (Root Mean Squared Error)**: Penalizes larger errors
- **R² Score**: Proportion of variance explained (0-1, higher is better)
- **Accuracy Percentage**: Simplified metric for business users

## Sample Data

The system includes seed data for testing:
- 80 historical freight records across 5 routes
- 150 historical coffee price records from Peru and Colombia
- 2 trained model metadata records

## Usage Examples

### Predict Freight Cost

```bash
curl -X POST "http://localhost:8000/api/v1/ml/predict-freight" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "origin_port": "Callao",
    "destination_port": "Hamburg",
    "weight_kg": 20000,
    "container_type": "40ft",
    "departure_date": "2025-03-15"
  }'
```

Response:
```json
{
  "predicted_cost_usd": 4850.50,
  "confidence_interval_low": 4200.00,
  "confidence_interval_high": 5500.00,
  "confidence_score": 0.85,
  "factors_considered": ["route", "weight", "container_type", "season"],
  "similar_historical_shipments": 12
}
```

### Predict Coffee Price

```bash
curl -X POST "http://localhost:8000/api/v1/ml/predict-coffee-price" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "origin_country": "Peru",
    "origin_region": "Cajamarca",
    "variety": "Caturra",
    "process_method": "Washed",
    "quality_grade": "AA",
    "cupping_score": 85.5,
    "certifications": ["Organic", "Fair Trade"],
    "forecast_date": "2025-03-15"
  }'
```

Response:
```json
{
  "predicted_price_usd_per_kg": 7.85,
  "confidence_interval_low": 7.20,
  "confidence_interval_high": 8.50,
  "confidence_score": 0.82,
  "market_comparison": "above_recent_average",
  "price_trend": "increasing"
}
```

## Future Enhancements

- **LightGBM**: Another gradient boosting alternative (similar interface, faster on large datasets)
- **Real-time Data**: Integration with ICE futures API, shipping APIs
- **Automated Retraining**: Scheduled model updates with new data
- **Quantile Regression**: Proper probabilistic confidence intervals for XGBoost
- **A/B Testing**: Compare model versions in production
- **Time Series Models**: ARIMA, LSTM for better temporal patterns
- **Market Sentiment**: Incorporate news and market sentiment analysis

## Notes

- Models gracefully degrade when data is sparse
- Predictions include uncertainty estimates
- Focus on explainability over complexity
- Regular retraining recommended as more data accumulates
- Model files stored as joblib binaries
- All services are async-compatible
- Type-safe with MyPy strict mode
