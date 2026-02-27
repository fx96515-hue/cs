"""
Seed ML training data

Revision ID: 0010_seed_ml_data
Revises: 0009_ml_prediction_tables
Create Date: 2025-12-29
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

import sqlalchemy as sa
from alembic import op

revision = "0010_seed_ml_data"
down_revision = "0009_ml_prediction_tables"
branch_labels = None
depends_on = None


def _build_freight_data(base_date: date) -> list[dict]:
    routes = [
        ("Callao", "Hamburg"),
        ("Callao", "Rotterdam"),
        ("Santos", "Hamburg"),
        ("Buenaventura", "Hamburg"),
        ("Manzanillo", "Hamburg"),
    ]
    container_types = ["20ft", "40ft"]
    carriers = ["Maersk", "MSC", "CMA CGM", "Hapag-Lloyd"]

    freight_data: list[dict] = []
    for i in range(80):
        origin, destination = routes[i % len(routes)]
        route = f"{origin}-{destination}"
        container = container_types[i % 2]
        carrier = carriers[i % len(carriers)]

        dept_date = base_date + timedelta(days=i * 7)
        season = f"Q{(dept_date.month - 1) // 3 + 1}"

        base_cost = 3000 if container == "20ft" else 5000
        route_multiplier = 1.0 + (i % len(routes)) * 0.15
        seasonal_var = 1.1 if season in {"Q3", "Q4"} else 1.0

        freight_cost = base_cost * route_multiplier * seasonal_var * (0.9 + (i % 20) * 0.01)
        weight = 18000 if container == "20ft" else 26000
        transit = 25 + (i % 5)
        arrival = dept_date + timedelta(days=transit)

        freight_data.append(
            {
                "route": route,
                "origin_port": origin,
                "destination_port": destination,
                "carrier": carrier,
                "container_type": container,
                "weight_kg": weight,
                "freight_cost_usd": round(freight_cost, 2),
                "transit_days": transit,
                "departure_date": dept_date,
                "arrival_date": arrival,
                "season": season,
                "fuel_price_index": 95.0 + (i % 20),
                "port_congestion_score": 40.0 + (i % 30),
            }
        )
    return freight_data


def _build_price_data(base_date: date) -> list[dict]:
    origins = [
        ("Peru", "Cajamarca"),
        ("Peru", "Cusco"),
        ("Peru", "Amazonas"),
        ("Colombia", "Huila"),
        ("Colombia", "NariÃ±o"),
    ]
    varieties = ["Caturra", "Bourbon", "Typica", "Catimor"]
    processes = ["Washed", "Natural", "Honey"]
    grades = ["AA", "AB", "A", "B"]

    price_data: list[dict] = []
    for i in range(150):
        country, region = origins[i % len(origins)]
        variety = varieties[i % len(varieties)]
        process = processes[i % len(processes)]
        grade = grades[i % len(grades)]
        record_date = base_date + timedelta(days=i * 3)

        base_price_kg = 5.0
        if grade == "AA":
            base_price_kg = 7.5
        elif grade == "AB":
            base_price_kg = 6.5

        if process == "Natural":
            base_price_kg *= 1.15
        elif process == "Honey":
            base_price_kg *= 1.10

        price_kg = base_price_kg * (0.85 + (i % 30) * 0.01)
        price_lb = price_kg / 2.205
        ice_c = 1.5 + (i % 50) * 0.01
        differential = price_lb - ice_c
        cupping = 82.0 + (i % 8)

        certifications: list[str] = []
        if i % 3 == 0:
            certifications.append("Organic")
        if i % 5 == 0:
            certifications.append("Fair Trade")

        price_data.append(
            {
                "date": record_date,
                "origin_country": country,
                "origin_region": region,
                "variety": variety,
                "process_method": process,
                "quality_grade": grade,
                "cupping_score": cupping,
                "certifications": certifications if certifications else None,
                "price_usd_per_kg": round(price_kg, 2),
                "price_usd_per_lb": round(price_lb, 2),
                "ice_c_price_usd_per_lb": round(ice_c, 2),
                "differential_usd_per_lb": round(differential, 2),
                "market_source": "actual_trade" if i % 2 == 0 else "market_estimate",
            }
        )
    return price_data


def upgrade() -> None:
    base_date = date(2024, 1, 1)

    freight_data = _build_freight_data(base_date)
    op.bulk_insert(
        sa.table(
            "freight_history",
            sa.column("route", sa.String),
            sa.column("origin_port", sa.String),
            sa.column("destination_port", sa.String),
            sa.column("carrier", sa.String),
            sa.column("container_type", sa.String),
            sa.column("weight_kg", sa.Integer),
            sa.column("freight_cost_usd", sa.Float),
            sa.column("transit_days", sa.Integer),
            sa.column("departure_date", sa.Date),
            sa.column("arrival_date", sa.Date),
            sa.column("season", sa.String),
            sa.column("fuel_price_index", sa.Float),
            sa.column("port_congestion_score", sa.Float),
        ),
        freight_data,
    )

    price_data = _build_price_data(base_date)
    op.bulk_insert(
        sa.table(
            "coffee_price_history",
            sa.column("date", sa.Date),
            sa.column("origin_country", sa.String),
            sa.column("origin_region", sa.String),
            sa.column("variety", sa.String),
            sa.column("process_method", sa.String),
            sa.column("quality_grade", sa.String),
            sa.column("cupping_score", sa.Float),
            sa.column("certifications", sa.JSON),
            sa.column("price_usd_per_kg", sa.Float),
            sa.column("price_usd_per_lb", sa.Float),
            sa.column("ice_c_price_usd_per_lb", sa.Float),
            sa.column("differential_usd_per_lb", sa.Float),
            sa.column("market_source", sa.String),
        ),
        price_data,
    )

    op.bulk_insert(
        sa.table(
            "ml_models",
            sa.column("model_name", sa.String),
            sa.column("model_type", sa.String),
            sa.column("model_version", sa.String),
            sa.column("training_date", sa.DateTime),
            sa.column("features_used", sa.JSON),
            sa.column("performance_metrics", sa.JSON),
            sa.column("training_data_count", sa.Integer),
            sa.column("model_file_path", sa.String),
            sa.column("status", sa.String),
        ),
        [
            {
                "model_name": "Freight Cost Predictor v1",
                "model_type": "freight_prediction",
                "model_version": "1.0.0",
                "training_date": datetime.now(),
                "features_used": ["route", "weight", "container_type", "season"],
                "performance_metrics": {
                    "mae": 250.0,
                    "rmse": 320.0,
                    "r2_score": 0.85,
                    "accuracy_percentage": 85.0,
                },
                "training_data_count": 80,
                "model_file_path": "/models/freight_v1.joblib",
                "status": "active",
            },
            {
                "model_name": "Coffee Price Predictor v1",
                "model_type": "price_prediction",
                "model_version": "1.0.0",
                "training_date": datetime.now(),
                "features_used": ["origin", "variety", "process", "grade", "cupping_score"],
                "performance_metrics": {
                    "mae": 0.45,
                    "rmse": 0.62,
                    "r2_score": 0.82,
                    "accuracy_percentage": 82.0,
                },
                "training_data_count": 150,
                "model_file_path": "/models/price_v1.joblib",
                "status": "active",
            },
        ],
    )


def downgrade() -> None:
    op.execute("DELETE FROM ml_models WHERE model_version = '1.0.0'")
    op.execute("DELETE FROM coffee_price_history")
    op.execute("DELETE FROM freight_history")
