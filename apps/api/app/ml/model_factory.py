"""ML model factory: creates the correct model implementation based on ML_MODEL_TYPE env var."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from app.ml.freight_model import FreightCostModel
    from app.ml.price_model import CoffeePriceModel
    from app.ml.xgboost_freight_model import XGBoostFreightCostModel
    from app.ml.xgboost_price_model import XGBoostCoffeePriceModel

    PriceModelType = Union[CoffeePriceModel, XGBoostCoffeePriceModel]
    FreightModelType = Union[FreightCostModel, XGBoostFreightCostModel]

_VALID_MODEL_TYPES = ("random_forest", "xgboost")

# Maps model class name -> canonical algorithm string stored in the DB.
_CLASS_TO_ALGORITHM: dict[str, str] = {
    "CoffeePriceModel": "random_forest",
    "FreightCostModel": "random_forest",
    "XGBoostCoffeePriceModel": "xgboost",
    "XGBoostFreightCostModel": "xgboost",
}


def _get_model_type() -> str:
    """Return the configured ML model type, defaulting to 'random_forest'."""
    from app.core.config import settings

    model_type = settings.ML_MODEL_TYPE.lower()
    if model_type not in _VALID_MODEL_TYPES:
        import logging

        logging.getLogger(__name__).warning(
            "Unknown ML_MODEL_TYPE %r – falling back to 'random_forest'.", model_type
        )
        return "random_forest"
    return model_type


def create_price_model() -> "PriceModelType":
    """Instantiate and return the configured coffee price prediction model.

    Returns:
        CoffeePriceModel when ML_MODEL_TYPE=random_forest (default).
        XGBoostCoffeePriceModel when ML_MODEL_TYPE=xgboost.
    """
    if _get_model_type() == "xgboost":
        from app.ml.xgboost_price_model import XGBoostCoffeePriceModel

        return XGBoostCoffeePriceModel()
    from app.ml.price_model import CoffeePriceModel

    return CoffeePriceModel()


def create_freight_model() -> "FreightModelType":
    """Instantiate and return the configured freight cost prediction model.

    Returns:
        FreightCostModel when ML_MODEL_TYPE=random_forest (default).
        XGBoostFreightCostModel when ML_MODEL_TYPE=xgboost.
    """
    if _get_model_type() == "xgboost":
        from app.ml.xgboost_freight_model import XGBoostFreightCostModel

        return XGBoostFreightCostModel()
    from app.ml.freight_model import FreightCostModel

    return FreightCostModel()


def algorithm_for_model(model: object) -> str:
    """Derive the canonical algorithm name from an instantiated model object.

    Avoids calling ``_get_model_type()`` a second time by inspecting the
    class name instead, keeping the algorithm string single-sourced.

    Args:
        model: An instantiated price or freight model.

    Returns:
        'xgboost' or 'random_forest'
    """
    class_name = type(model).__name__
    return _CLASS_TO_ALGORITHM.get(class_name, "random_forest")
