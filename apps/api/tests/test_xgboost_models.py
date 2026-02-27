"""Tests for XGBoost ML models and factory pattern."""

import os
import pytest
import pandas as pd
import numpy as np
import tempfile

# Set required env vars before importing app modules
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault(
    "JWT_SECRET",
    "test_jwt_secret_key_for_testing_only_must_be_at_least_32_chars",
)
os.environ.setdefault("ML_MODEL_TYPE", "random_forest")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def price_training_df():
    """Minimal coffee price training DataFrame."""
    rng = np.random.default_rng(42)
    n = 30
    return pd.DataFrame(
        {
            "origin_country": rng.choice(["Peru", "Colombia"], n),
            "origin_region": rng.choice(["Cajamarca", "Huila"], n),
            "variety": rng.choice(["Caturra", "Bourbon"], n),
            "process_method": rng.choice(["washed", "natural"], n),
            "quality_grade": rng.choice(["AA", "A"], n),
            "market_source": rng.choice(["direct", "spot"], n),
            "cupping_score": rng.uniform(80, 90, n),
            "certifications": [["Organic"] if i % 2 == 0 else [] for i in range(n)],
            "ice_c_price_usd_per_lb": rng.uniform(1.0, 2.5, n),
            "date": pd.date_range("2024-01-01", periods=n, freq="W"),
            "price_usd_per_kg": rng.uniform(5.0, 10.0, n),
        }
    )


@pytest.fixture
def freight_training_df():
    """Minimal freight training DataFrame."""
    rng = np.random.default_rng(42)
    n = 30
    return pd.DataFrame(
        {
            "route": rng.choice(["Callao-Hamburg", "Santos-Rotterdam"], n),
            "container_type": rng.choice(["20ft", "40ft"], n),
            "season": rng.choice(["Q1", "Q2", "Q3", "Q4"], n),
            "carrier": rng.choice(["Maersk", "MSC"], n),
            "weight_kg": rng.integers(5000, 20000, n),
            "fuel_price_index": rng.uniform(90, 120, n),
            "port_congestion_score": rng.uniform(30, 80, n),
            "freight_cost_usd": rng.uniform(2000, 8000, n),
        }
    )


# ---------------------------------------------------------------------------
# Random Forest model tests (existing models with new get_feature_importance)
# ---------------------------------------------------------------------------


class TestCoffeePriceModelRF:
    def test_train_predict(self, price_training_df):
        from app.ml.price_model import CoffeePriceModel

        m = CoffeePriceModel()
        X, y = m.prepare_features(price_training_df)
        assert y is not None
        m.train(X, y)
        preds = m.predict(X)
        assert len(preds) == len(price_training_df)

    def test_predict_with_confidence(self, price_training_df):
        from app.ml.price_model import CoffeePriceModel

        m = CoffeePriceModel()
        X, y = m.prepare_features(price_training_df)
        m.train(X, y)
        preds, low, high = m.predict_with_confidence(X)
        assert np.all(high >= low)
        assert np.all(preds >= low)
        assert np.all(preds <= high)

    def test_feature_importance(self, price_training_df):
        from app.ml.price_model import CoffeePriceModel

        m = CoffeePriceModel()
        X, y = m.prepare_features(price_training_df)
        m.train(X, y)
        importance = m.get_feature_importance()
        assert isinstance(importance, dict)
        assert len(importance) == 9  # 9 features
        # Values should sum to ~1
        assert abs(sum(importance.values()) - 1.0) < 1e-6

    def test_save_load(self, price_training_df):
        from app.ml.price_model import CoffeePriceModel

        m = CoffeePriceModel()
        X, y = m.prepare_features(price_training_df)
        m.train(X, y)

        with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as f:
            path = f.name
        try:
            m.save(path)
            m2 = CoffeePriceModel()
            m2.load(path)
            preds2 = m2.predict(X)
            np.testing.assert_array_almost_equal(m.predict(X), preds2)
        finally:
            os.unlink(path)


class TestFreightCostModelRF:
    def test_train_predict(self, freight_training_df):
        from app.ml.freight_model import FreightCostModel

        m = FreightCostModel()
        X, y = m.prepare_features(freight_training_df)
        assert y is not None
        m.train(X, y)
        preds = m.predict(X)
        assert len(preds) == len(freight_training_df)

    def test_feature_importance(self, freight_training_df):
        from app.ml.freight_model import FreightCostModel

        m = FreightCostModel()
        X, y = m.prepare_features(freight_training_df)
        m.train(X, y)
        importance = m.get_feature_importance()
        assert isinstance(importance, dict)
        assert len(importance) == 6  # 6 features
        assert abs(sum(importance.values()) - 1.0) < 1e-6


# ---------------------------------------------------------------------------
# XGBoost model tests
# ---------------------------------------------------------------------------


class TestXGBoostCoffeePriceModel:
    def test_train_predict(self, price_training_df):
        from app.ml.xgboost_price_model import XGBoostCoffeePriceModel

        m = XGBoostCoffeePriceModel()
        X, y = m.prepare_features(price_training_df)
        assert y is not None
        m.train(X, y)
        preds = m.predict(X)
        assert len(preds) == len(price_training_df)
        assert not np.any(np.isnan(preds))

    def test_predict_with_confidence(self, price_training_df):
        from app.ml.xgboost_price_model import XGBoostCoffeePriceModel

        m = XGBoostCoffeePriceModel()
        X, y = m.prepare_features(price_training_df)
        m.train(X, y)
        preds, low, high = m.predict_with_confidence(X)
        assert np.all(high >= low)
        assert np.all(preds >= low)
        assert np.all(preds <= high)

    def test_feature_importance(self, price_training_df):
        from app.ml.xgboost_price_model import XGBoostCoffeePriceModel

        m = XGBoostCoffeePriceModel()
        X, y = m.prepare_features(price_training_df)
        m.train(X, y)
        importance = m.get_feature_importance()
        assert isinstance(importance, dict)
        assert len(importance) == 9  # Same 9 features as RF
        assert abs(sum(importance.values()) - 1.0) < 1e-6
        # All importance values should be non-negative
        assert all(v >= 0 for v in importance.values())

    def test_save_load(self, price_training_df):
        from app.ml.xgboost_price_model import XGBoostCoffeePriceModel

        m = XGBoostCoffeePriceModel()
        X, y = m.prepare_features(price_training_df)
        m.train(X, y)

        with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as f:
            path = f.name
        try:
            m.save(path)
            m2 = XGBoostCoffeePriceModel()
            m2.load(path)
            np.testing.assert_array_almost_equal(m.predict(X), m2.predict(X))
        finally:
            os.unlink(path)

    def test_prepare_features_missing_cols(self):
        """prepare_features should handle missing optional columns gracefully."""
        from app.ml.xgboost_price_model import XGBoostCoffeePriceModel

        df = pd.DataFrame(
            {
                "origin_country": ["Peru"],
                "origin_region": ["Cajamarca"],
                "variety": ["Caturra"],
                "process_method": ["washed"],
                "quality_grade": ["AA"],
                "price_usd_per_kg": [7.5],
            }
        )
        m = XGBoostCoffeePriceModel()
        X, y = m.prepare_features(df)
        assert y is not None
        assert X.shape[1] == 9


class TestXGBoostFreightCostModel:
    def test_train_predict(self, freight_training_df):
        from app.ml.xgboost_freight_model import XGBoostFreightCostModel

        m = XGBoostFreightCostModel()
        X, y = m.prepare_features(freight_training_df)
        assert y is not None
        m.train(X, y)
        preds = m.predict(X)
        assert len(preds) == len(freight_training_df)
        assert not np.any(np.isnan(preds))

    def test_feature_importance(self, freight_training_df):
        from app.ml.xgboost_freight_model import XGBoostFreightCostModel

        m = XGBoostFreightCostModel()
        X, y = m.prepare_features(freight_training_df)
        m.train(X, y)
        importance = m.get_feature_importance()
        assert isinstance(importance, dict)
        assert len(importance) == 6
        assert abs(sum(importance.values()) - 1.0) < 1e-6

    def test_save_load(self, freight_training_df):
        from app.ml.xgboost_freight_model import XGBoostFreightCostModel

        m = XGBoostFreightCostModel()
        X, y = m.prepare_features(freight_training_df)
        m.train(X, y)

        with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as f:
            path = f.name
        try:
            m.save(path)
            m2 = XGBoostFreightCostModel()
            m2.load(path)
            np.testing.assert_array_almost_equal(m.predict(X), m2.predict(X))
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Factory tests
# ---------------------------------------------------------------------------


class TestModelFactory:
    def test_default_returns_rf(self, monkeypatch):
        """Without ML_MODEL_TYPE set to xgboost, factory returns Random Forest."""
        monkeypatch.setenv("ML_MODEL_TYPE", "random_forest")

        # Reload settings so the monkeypatched value is picked up
        import importlib
        import app.core.config as config_module

        importlib.reload(config_module)

        import app.ml.model_factory as factory_module

        importlib.reload(factory_module)

        from app.ml.model_factory import create_price_model, create_freight_model
        from app.ml.price_model import CoffeePriceModel
        from app.ml.freight_model import FreightCostModel

        assert isinstance(create_price_model(), CoffeePriceModel)
        assert isinstance(create_freight_model(), FreightCostModel)

    def test_xgboost_flag_returns_xgboost(self, monkeypatch):
        """With ML_MODEL_TYPE=xgboost, factory returns XGBoost models."""
        monkeypatch.setenv("ML_MODEL_TYPE", "xgboost")

        import importlib
        import app.core.config as config_module

        importlib.reload(config_module)

        import app.ml.model_factory as factory_module

        importlib.reload(factory_module)

        from app.ml.model_factory import create_price_model, create_freight_model
        from app.ml.xgboost_price_model import XGBoostCoffeePriceModel
        from app.ml.xgboost_freight_model import XGBoostFreightCostModel

        assert isinstance(create_price_model(), XGBoostCoffeePriceModel)
        assert isinstance(create_freight_model(), XGBoostFreightCostModel)

    def test_unknown_model_type_falls_back_to_rf(self, monkeypatch):
        """Unknown ML_MODEL_TYPE should fall back to random_forest."""
        monkeypatch.setenv("ML_MODEL_TYPE", "lightgbm_future")

        import importlib
        import app.core.config as config_module

        importlib.reload(config_module)

        import app.ml.model_factory as factory_module

        importlib.reload(factory_module)

        from app.ml.model_factory import create_price_model
        from app.ml.price_model import CoffeePriceModel

        assert isinstance(create_price_model(), CoffeePriceModel)

    def test_algorithm_for_model_rf(self, monkeypatch):
        monkeypatch.setenv("ML_MODEL_TYPE", "random_forest")

        import importlib
        import app.core.config as config_module

        importlib.reload(config_module)

        import app.ml.model_factory as factory_module

        importlib.reload(factory_module)

        from app.ml.model_factory import algorithm_for_model, create_price_model

        model = create_price_model()
        assert algorithm_for_model(model) == "random_forest"

    def test_algorithm_for_model_xgboost(self, monkeypatch):
        monkeypatch.setenv("ML_MODEL_TYPE", "xgboost")

        import importlib
        import app.core.config as config_module

        importlib.reload(config_module)

        import app.ml.model_factory as factory_module

        importlib.reload(factory_module)

        from app.ml.model_factory import algorithm_for_model, create_price_model

        model = create_price_model()
        assert algorithm_for_model(model) == "xgboost"
