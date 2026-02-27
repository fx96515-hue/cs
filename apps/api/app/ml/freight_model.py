"""Freight cost prediction ML model."""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import joblib


class FreightCostModel:
    """Machine learning model for freight cost prediction."""

    def __init__(self) -> None:
        self.model = RandomForestRegressor(
            n_estimators=100, max_depth=10, random_state=42
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
                    # Fit if training
                    if col in df.columns and not df[col].empty:
                        self.encoders[col].fit(df[col].astype(str))
                try:
                    df[f"{col}_encoded"] = self.encoders[col].transform(
                        df[col].astype(str)
                    )
                except ValueError:
                    # Handle unknown labels during prediction
                    df[f"{col}_encoded"] = 0

        # Normalize weight
        if "weight_kg" in df.columns:
            df["weight_normalized"] = df["weight_kg"] / 20000.0  # Normalize by max

        # Handle missing optional features
        if "fuel_price_index" in df.columns:
            df["fuel_price_index"] = df["fuel_price_index"].fillna(100.0)
        else:
            df["fuel_price_index"] = 100.0

        if "port_congestion_score" in df.columns:
            df["port_congestion_score"] = df["port_congestion_score"].fillna(50.0)
        else:
            df["port_congestion_score"] = 50.0

        # Select features for model
        feature_cols = [
            "route_encoded",
            "container_type_encoded",
            "season_encoded",
            "weight_normalized",
            "fuel_price_index",
            "port_congestion_score",
        ]

        X = df[feature_cols]

        # Return target if available (training)
        y = df["freight_cost_usd"] if "freight_cost_usd" in df.columns else None

        return X, y

    def train(self, X: pd.DataFrame, y: pd.Series | None) -> None:
        """Train the freight cost model.

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
        """Make predictions with confidence intervals.

        Args:
            X: Feature dataframe

        Returns:
            Tuple of (predictions, lower_bound, upper_bound)
        """
        predictions = self.predict(X)

        # Use standard deviation from trees for confidence
        tree_predictions = np.array(
            [tree.predict(X) for tree in self.model.estimators_]
        )
        std = np.std(tree_predictions, axis=0)

        lower_bound = predictions - 1.96 * std
        upper_bound = predictions + 1.96 * std

        return predictions, lower_bound, upper_bound

    def save(self, path: str) -> None:
        """Save model to disk.

        Args:
            path: File path for saving the model
        """
        model_data = {
            "model": self.model,
            "encoders": self.encoders,
            "algorithm": "random_forest",
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

    def get_feature_importance(self) -> dict[str, float]:
        """Return feature importances from the trained Random Forest model.

        Returns:
            Mapping of feature name -> importance score (normalised to sum 1).
        """
        feature_names = [
            "route_encoded",
            "container_type_encoded",
            "season_encoded",
            "weight_normalized",
            "fuel_price_index",
            "port_congestion_score",
        ]
        importance_scores = self.model.feature_importances_
        total = importance_scores.sum()
        if total == 0:
            normalised = importance_scores
        else:
            normalised = importance_scores / total
        return dict(zip(feature_names, normalised.tolist()))
