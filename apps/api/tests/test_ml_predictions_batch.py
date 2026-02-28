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
