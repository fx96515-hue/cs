"""XGBoost coffee price prediction ML model."""

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
import joblib

try:
    from xgboost import XGBRegressor

    _XGBOOST_AVAILABLE = True
except ImportError:  # pragma: no cover
    _XGBOOST_AVAILABLE = False


class XGBoostCoffeePriceModel:
    """XGBoost machine learning model for coffee price prediction.

    Implements the same interface as CoffeePriceModel (train / predict /
    predict_with_confidence / save / load) plus get_feature_importance().
    """

    FEATURE_NAMES = [
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

        # Handle cupping score
        if "cupping_score" in df.columns:
            df["cupping_score"] = df["cupping_score"].fillna(82.0)
        else:
            df["cupping_score"] = 82.0

        # Handle ICE C price
        if "ice_c_price_usd_per_lb" in df.columns:
            df["ice_c_price_normalized"] = df["ice_c_price_usd_per_lb"] / 2.0
        else:
            df["ice_c_price_normalized"] = 1.0

        # Certification count from JSON/list
        if "certifications" in df.columns:
            df["certification_count"] = df["certifications"].apply(
                lambda x: len(x) if isinstance(x, list) else 0
            )
        else:
            df["certification_count"] = 0

        # Extract month for seasonality
        if "date" in df.columns:
            df["month"] = pd.to_datetime(df["date"]).dt.month
        else:
            df["month"] = 1

        # Ensure all feature columns exist
        for col in self.FEATURE_NAMES:
            if col not in df.columns:
                df[col] = 0

        X = df[self.FEATURE_NAMES]
        y = df["price_usd_per_kg"] if "price_usd_per_kg" in df.columns else None

        return X, y

    def train(self, X: pd.DataFrame, y: pd.Series | None) -> None:
        """Train the XGBoost coffee price model.

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
        """Make predictions with approximate confidence intervals.

        XGBoost does not natively output per-tree predictions the same way as
        Random Forest, so we use a ±10 % heuristic as the confidence band.
        For production use, quantile regression or conformal prediction should
        be used instead.

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
