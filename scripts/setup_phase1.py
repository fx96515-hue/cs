"""Conservative helper for reviewing Phase 1 setup.

This script does not mutate the database. It only prints the expected migration
target and the additive tables introduced for the PR721 enterprise integration.
"""

from __future__ import annotations


def main() -> None:
    print("CoffeeStudio Phase 1 review helper")
    print("Expected migration target: 0020_full_stack_data_models")
    print("Additive tables:")
    for table in (
        "weather_agronomic_data",
        "social_sentiment_data",
        "shipment_api_events",
        "ml_features_cache",
        "data_lineage_log",
        "source_health_metrics",
    ):
        print(f"- {table}")
    print("Apply with Alembic, not with raw SQL scripts.")


if __name__ == "__main__":
    main()
