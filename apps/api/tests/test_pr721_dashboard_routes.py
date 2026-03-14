from datetime import datetime, timezone

from app.models.coffee_price_history import CoffeePriceHistory
from app.models.freight_history import FreightHistory
from app.models.market import MarketObservation
from app.models.ml_model import MLModel
from app.models.news_item import NewsItem


def test_pipeline_status_endpoint(client, auth_headers, db):
    db.add(
        MarketObservation(
            key="FX:USD_EUR",
            value=0.92,
            unit=None,
            currency=None,
            observed_at=datetime.now(timezone.utc),
        )
    )
    db.add(
        MarketObservation(
            key="COFFEE_C:USD_LB",
            value=2.45,
            unit="lb",
            currency="USD",
            observed_at=datetime.now(timezone.utc),
        )
    )
    db.add(
        NewsItem(
            topic="market",
            title="Coffee market update",
            url="https://example.com/news/1",
            published_at=datetime.now(timezone.utc),
            retrieved_at=datetime.now(timezone.utc),
        )
    )
    db.commit()

    response = client.get("/pipeline/status", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["totalSources"] >= 5
    assert {"online", "degraded", "offline"} <= data.keys()
    assert data["providerCatalog"]["total_sources"] >= data["totalSources"]


def test_pipeline_sources_endpoint(client, auth_headers):
    response = client.get("/pipeline/sources", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(item["name"] == "Coffee Prices" for item in data)
    assert any(item["name"] == "Peru Macro" for item in data)


def test_features_quality_report_endpoint(client, auth_headers, db):
    db.add(
        MLModel(
            model_name="freight-model",
            model_type="freight_cost",
            model_version="v1",
            training_date=datetime.now(timezone.utc),
            features_used=["fuel_price_index", "port_congestion_score"],
            performance_metrics={"mae": 1.2},
            training_data_count=25,
            model_file_path="models/missing.joblib",
            status="active",
            algorithm="random_forest",
        )
    )
    db.add(
        FreightHistory(
            route="Callao-Hamburg",
            origin_port="Callao",
            destination_port="Hamburg",
            carrier="Test Carrier",
            container_type="20ft",
            weight_kg=1000,
            freight_cost_usd=2400,
            transit_days=32,
            departure_date=datetime(2026, 3, 1, tzinfo=timezone.utc).date(),
            arrival_date=datetime(2026, 4, 2, tzinfo=timezone.utc).date(),
            season="Q1",
        )
    )
    db.add(
        CoffeePriceHistory(
            date=datetime(2026, 3, 1, tzinfo=timezone.utc).date(),
            origin_country="Peru",
            origin_region="Cajamarca",
            variety="Caturra",
            process_method="Washed",
            quality_grade="Specialty",
            cupping_score=85.5,
            certifications=["Organic"],
            price_usd_per_kg=7.2,
            price_usd_per_lb=3.27,
            ice_c_price_usd_per_lb=2.45,
            differential_usd_per_lb=0.82,
            market_source="actual_trade",
        )
    )
    db.commit()

    response = client.get("/features/quality-report", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["totalFeatures"] == 2
    assert data["trainingRecords"] == 2


def test_features_importance_endpoint(client, auth_headers, db):
    db.add(
        MLModel(
            model_name="price-model",
            model_type="coffee_price",
            model_version="v2",
            training_date=datetime.now(timezone.utc),
            features_used=["ice_c_price_usd_per_lb", "quality_grade", "certifications_premium"],
            performance_metrics={"mae": 0.8},
            training_data_count=40,
            model_file_path="models/missing.joblib",
            status="active",
            algorithm="random_forest",
        )
    )
    db.commit()

    response = client.get("/features/importance", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(category["name"] == "Preis-Features" for category in data)


def test_features_catalog_endpoint(client, auth_headers):
    response = client.get("/features/catalog", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(category["name"] == "Cross-Features" for category in data)
    assert any(feature["name"] == "freight_to_price_ratio" for category in data for feature in category["features"])


def test_features_import_template_endpoint(client, auth_headers):
    response = client.get("/features/import-template/price", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["dataType"] == "price"
    assert "price_usd_per_kg" in data["columns"]
