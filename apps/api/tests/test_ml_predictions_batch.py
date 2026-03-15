"""Tests for ML batch prediction endpoints."""

from datetime import date


def test_batch_freight_predictions(client, auth_headers):
    payload = {
        "requests": [
            {
                "origin_port": "Callao",
                "destination_port": "Hamburg",
                "weight_kg": 20000,
                "container_type": "40ft",
                "departure_date": date.today().isoformat(),
            }
        ]
    }

    response = client.post(
        "/ml/predict-freight/batch", json=payload, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert isinstance(data["errors"], list)


def test_batch_coffee_price_predictions(client, auth_headers):
    payload = {
        "requests": [
            {
                "origin_country": "Peru",
                "origin_region": "Cajamarca",
                "variety": "Caturra",
                "process_method": "washed",
                "quality_grade": "specialty",
                "cupping_score": 86.0,
                "certifications": ["Organic"],
                "forecast_date": date.today().isoformat(),
            }
        ]
    }

    response = client.post(
        "/ml/predict-coffee-price/batch", json=payload, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert isinstance(data["errors"], list)


def test_import_freight_data_error_is_sanitized(client, auth_headers, monkeypatch):
    async def _raise_import_error(*args, **kwargs):
        raise RuntimeError("sensitive freight import stacktrace")

    monkeypatch.setattr(
        "app.services.ml.data_collection.DataCollectionService.import_freight_data",
        _raise_import_error,
    )

    payload = [
        {
            "route": "Callao-Hamburg",
            "origin_port": "Callao",
            "destination_port": "Hamburg",
            "carrier": "Test Carrier",
            "container_type": "40ft",
            "weight_kg": 20000,
            "freight_cost_usd": 4200.5,
            "transit_days": 28,
            "departure_date": "2026-01-10",
            "arrival_date": "2026-02-07",
            "season": "summer",
            "fuel_price_index": 1.1,
            "port_congestion_score": 0.3,
        }
    ]

    response = client.post("/ml/data/import-freight", json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Import failed"


def test_import_price_data_error_is_sanitized(client, auth_headers, monkeypatch):
    async def _raise_import_error(*args, **kwargs):
        raise RuntimeError("sensitive price import stacktrace")

    monkeypatch.setattr(
        "app.services.ml.data_collection.DataCollectionService.import_price_data",
        _raise_import_error,
    )

    payload = [
        {
            "date": "2026-01-10",
            "origin_country": "Peru",
            "origin_region": "Cajamarca",
            "variety": "Caturra",
            "process_method": "washed",
            "quality_grade": "specialty",
            "cupping_score": 86.5,
            "certifications": ["Organic"],
            "price_usd_per_kg": 6.8,
            "price_usd_per_lb": 3.08,
            "ice_c_price_usd_per_lb": 2.4,
            "differential_usd_per_lb": 0.68,
            "market_source": "test",
        }
    ]

    response = client.post("/ml/data/import-prices", json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Import failed"
