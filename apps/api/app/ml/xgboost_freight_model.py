"""XGBoost freight cost prediction ML model."""

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
import joblib

try:
    from xgboost import XGBRegressor

    _XGBOOST_AVAILABLE = True
except ImportError:  # pragma: no cover
    _XGBOOST_AVAILABLE = False


class XGBoostFreightCostModel:
    """XGBoost machine learning model for freight cost prediction.

    Implements the same interface as FreightCostModel (train / predict /
    predict_with_confidence / save / load) plus get_feature_importance().
    """

    FEATURE_NAMES = [
        "route_encoded",
        "container_type_encoded",
        "season_encoded",
        "weight_normalized",
        "fuel_price_index",
        "port_congestion_score",
    ]

    def __init__(self) -> None:
        if not _XGBOOST_AVAILABLE:
            raise ImportError(
                "xgboost is not installed. Add xgboost>=2.0.0 to requirements.txt."
            )
        self.model = XGBRegressor(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1,
            tree_method="hist",
        )
        self.encoders: dict[str, LabelEncoder] = {}

    def prepare_features(
        self, data: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.Series | None]:
        """Feature engineering for freight prediction.

        Args:
            data: Raw freight data with columns like route, container_type, etc.

        Returns:
            Tuple of (X features, y target) or (X features, None) for prediction
        """
        df = data.copy()

        # Encode categorical features
        categorical_cols = ["route", "container_type", "season", "carrier"]
        for col in categorical_cols:
            if col in df.columns:
                if col not in self.encoders:
                    self.encoders[col] = LabelEncoder()
                    if not df[col].empty:
                        self.encoders[col].fit(df[col].astype(str))
                try:
                    df[f"{col}_encoded"] = self.encoders[col].transform(
                        df[col].astype(str)
                    )
                except ValueError:
                    # Handle unknown labels at the element level: map known
                    # categories via the fitted classes_, default unknowns to 0.
                    class_to_index = {
                        cls: idx for idx, cls in enumerate(self.encoders[col].classes_)
                    }
                    df[f"{col}_encoded"] = (
                        df[col].astype(str).map(class_to_index).fillna(0).astype(int)
                    )

        # Normalize weight
        if "weight_kg" in df.columns:
            df["weight_normalized"] = df["weight_kg"] / 20000.0

        # Handle missing optional features
        if "fuel_price_index" in df.columns:
            df["fuel_price_index"] = df["fuel_price_index"].fillna(100.0)
        else:
            df["fuel_price_index"] = 100.0

        if "port_congestion_score" in df.columns:
            df["port_congestion_score"] = df["port_congestion_score"].fillna(50.0)
        else:
            df["port_congestion_score"] = 50.0

        # Ensure all feature columns exist
        for col in self.FEATURE_NAMES:
            if col not in df.columns:
                df[col] = 0

        X = df[self.FEATURE_NAMES]
        y = df["freight_cost_usd"] if "freight_cost_usd" in df.columns else None

        return X, y

    def train(self, X: pd.DataFrame, y: pd.Series | None) -> None:
        """Train the XGBoost freight cost model.

        Args:
            X: Feature dataframe
            y: Target series (freight costs)
        """
        # y may be Optional at type-check time; callers should ensure it's not None.
        self.model.fit(X, y)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make freight cost predictions.

        Args:
            X: Feature dataframe

        Returns:
            Array of predicted freight costs
        """
        return self.model.predict(X)

    def predict_with_confidence(
        self, X: pd.DataFrame
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Make predictions with approximate confidence intervals.

        Uses a ±10 % heuristic as the confidence band.

        Args:
            X: Feature dataframe

        Returns:
            Tuple of (predictions, lower_bound, upper_bound)
        """
        predictions = self.predict(X)
        margin = np.abs(predictions) * 0.10
        lower_bound = predictions - margin
        upper_bound = predictions + margin
        return predictions, lower_bound, upper_bound

    def get_feature_importance(self) -> dict[str, float]:
        """Return feature importances (gain) from the trained XGBoost model.

        Returns:
            Mapping of feature name -> importance score (normalised to sum 1).

        Raises:
            RuntimeError: If model has not been trained yet.
        """
        importance_scores = self.model.feature_importances_
        total = importance_scores.sum()
        if total == 0:
            normalised = importance_scores
        else:
            normalised = importance_scores / total
        return dict(zip(self.FEATURE_NAMES, normalised.tolist()))

    def save(self, path: str) -> None:
        """Save model to disk.

        Args:
            path: File path for saving the model
        """
        model_data = {
            "model": self.model,
            "encoders": self.encoders,
            "algorithm": "xgboost",
        }
        joblib.dump(model_data, path)

    def load(self, path: str) -> None:
        """Load model from disk.

        Args:
            path: File path for loading the model
        """
        model_data = joblib.load(path)
        self.model = model_data["model"]
        self.encoders = model_data["encoders"]
