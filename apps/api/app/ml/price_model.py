"""Coffee price prediction ML model."""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import joblib


class CoffeePriceModel:
    """Machine learning model for coffee price prediction."""

    def __init__(self) -> None:
        self.model = RandomForestRegressor(
            n_estimators=100, max_depth=10, random_state=42
        )
        self.encoders: dict[str, LabelEncoder] = {}

    def prepare_features(
        self, data: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.Series | None]:
        """Feature engineering for coffee price prediction.

        Args:
            data: Raw coffee price data

        Returns:
            Tuple of (X features, y target) or (X features, None) for prediction
        """
        df = data.copy()

        # Encode categorical features
        categorical_cols = [
            "origin_country",
            "origin_region",
            "variety",
            "process_method",
            "quality_grade",
            "market_source",
        ]
        for col in categorical_cols:
            if col in df.columns:
                if col not in self.encoders:
                    self.encoders[col] = LabelEncoder()
                    if col in df.columns and not df[col].empty:
                        self.encoders[col].fit(df[col].astype(str))
                try:
                    df[f"{col}_encoded"] = self.encoders[col].transform(
                        df[col].astype(str)
                    )
                except ValueError:
                    # Handle unknown labels
                    df[f"{col}_encoded"] = 0

        # Handle cupping score
        if "cupping_score" in df.columns:
            df["cupping_score"] = df["cupping_score"].fillna(82.0)  # Default score
        else:
            df["cupping_score"] = 82.0

        # Handle ICE C price
        if "ice_c_price_usd_per_lb" in df.columns:
            df["ice_c_price_normalized"] = df["ice_c_price_usd_per_lb"] / 2.0
        else:
            df["ice_c_price_normalized"] = 1.0

        # Certification count from JSON
        if "certifications" in df.columns:
            df["certification_count"] = df["certifications"].apply(
                lambda x: len(x) if isinstance(x, list) else 0
            )
        else:
            df["certification_count"] = 0

        # Extract month/season if date available
        if "date" in df.columns:
            df["month"] = pd.to_datetime(df["date"]).dt.month
        else:
            df["month"] = 1

        # Select features for model
        feature_cols = [
            "origin_country_encoded",
            "origin_region_encoded",
            "variety_encoded",
            "process_method_encoded",
            "quality_grade_encoded",
            "cupping_score",
            "certification_count",
            "ice_c_price_normalized",
            "month",
        ]

        X = df[feature_cols]

        # Return target if available
        y = df["price_usd_per_kg"] if "price_usd_per_kg" in df.columns else None

        return X, y

    def train(self, X: pd.DataFrame, y: pd.Series | None) -> None:
        """Train the coffee price model.

        Args:
            X: Feature dataframe
            y: Target series (prices)
        """
        # y may be Optional at type-check time; callers should ensure it's not None.
        self.model.fit(X, y)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make price predictions.

        Args:
            X: Feature dataframe

        Returns:
            Array of predicted prices
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
            "origin_country_encoded",
            "origin_region_encoded",
            "variety_encoded",
            "process_method_encoded",
            "quality_grade_encoded",
            "cupping_score",
            "certification_count",
            "ice_c_price_normalized",
            "month",
        ]
        importance_scores = self.model.feature_importances_
        total = importance_scores.sum()
        if total == 0:
            normalised = importance_scores
        else:
            normalised = importance_scores / total
        return dict(zip(feature_names, normalised.tolist()))
