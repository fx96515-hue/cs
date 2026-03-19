"""Shipping provider catalog for PR721 integration."""

from __future__ import annotations

import os
from typing import Any


def _provider_entry(
    *,
    name: str,
    group: str,
    mode: str,
    configured: bool,
    coverage: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "name": name,
        "group": group,
        "mode": mode,
        "configured": configured,
        "coverage": coverage,
        "notes": notes,
    }


class AISStreamProvider:
    SOURCE_NAME = "AIS Stream"

    @staticmethod
    def provider_status() -> dict[str, Any]:
        return _provider_entry(
            name=AISStreamProvider.SOURCE_NAME,
            group="shipping",
            mode="optional",
            configured=bool(os.getenv("AIS_API_KEY") or os.getenv("AISSTREAM_API_KEY")),
            coverage="Vessel telemetry",
            notes="Optional live vessel tracking source.",
        )


class MarineTrafficProvider:
    SOURCE_NAME = "MarineTraffic"

    PORTS = {
        "PEAPU": {"name": "Callao", "country": "Peru"},
        "PEPAI": {"name": "Paita", "country": "Peru"},
        "DEHAM": {"name": "Hamburg", "country": "Germany"},
        "DEBRV": {"name": "Bremerhaven", "country": "Germany"},
    }

    @staticmethod
    def provider_status() -> dict[str, Any]:
        return _provider_entry(
            name=MarineTrafficProvider.SOURCE_NAME,
            group="shipping",
            mode="optional",
            configured=bool(os.getenv("MARINETRAFFIC_API_KEY")),
            coverage="Port and congestion intelligence",
            notes="Optional commercial provider for port conditions.",
        )

    @staticmethod
    def fetch_port_catalog() -> list[dict[str, str]]:
        return [
            {
                "port_code": code,
                "port_name": payload["name"],
                "country": payload["country"],
            }
            for code, payload in MarineTrafficProvider.PORTS.items()
        ]


class ShippingProvider:
    @staticmethod
    def provider_catalog() -> list[dict[str, Any]]:
        return [
            AISStreamProvider.provider_status(),
            MarineTrafficProvider.provider_status(),
        ]

    @staticmethod
    def fetch_port_status() -> list[dict[str, str]]:
        return MarineTrafficProvider.fetch_port_catalog()

    @staticmethod
    def to_shipment_event(position_data: dict[str, Any]) -> dict[str, Any]:
        return {
            "vessel_imo": position_data.get("vessel_imo"),
            "vessel_mmsi": position_data.get("mmsi")
            or position_data.get("vessel_mmsi"),
            "vessel_name": position_data.get("vessel_name"),
            "vessel_type": position_data.get("vessel_type"),
            "latitude": position_data.get("latitude"),
            "longitude": position_data.get("longitude"),
            "speed_knots": position_data.get("speed_knots"),
            "course": position_data.get("course"),
            "event_type": position_data.get("event_type", "position_update"),
            "event_time": position_data.get("timestamp")
            or position_data.get("event_time"),
            "source": position_data.get("source", "shipping-provider"),
            "raw_data": position_data,
        }
