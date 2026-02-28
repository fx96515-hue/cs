"""Data collection service for ML training data."""

from datetime import datetime
from typing import Any
from sqlalchemy.orm import Session

from app.models.freight_history import FreightHistory
from app.models.coffee_price_history import CoffeePriceHistory


class DataCollectionService:
    """Service for collecting and managing ML training data."""

    def __init__(self, db: Session):
        self.db = db

    async def import_freight_data(self, data: list[dict[str, Any]]) -> int:
        """Import historical freight data.

        Args:
            data: List of freight record dictionaries

        Returns:
            Number of records imported
        """
        imported_count = 0

        for record in data:
            freight = FreightHistory(
                route=record["route"],
                origin_port=record["origin_port"],
                destination_port=record["destination_port"],
                carrier=record["carrier"],
                container_type=record["container_type"],
                weight_kg=record["weight_kg"],
                freight_cost_usd=record["freight_cost_usd"],
                transit_days=record["transit_days"],
                departure_date=record["departure_date"],
                arrival_date=record["arrival_date"],
                season=record["season"],
                fuel_price_index=record.get("fuel_price_index"),
                port_congestion_score=record.get("port_congestion_score"),
            )
            self.db.add(freight)
            imported_count += 1

        self.db.commit()
        return imported_count

    async def import_price_data(self, data: list[dict[str, Any]]) -> int:
        """Import historical coffee price data.

        Args:
            data: List of price record dictionaries

        Returns:
            Number of records imported
        """
        imported_count = 0

        for record in data:
            price_record = CoffeePriceHistory(
                date=record["date"],
                origin_country=record["origin_country"],
                origin_region=record["origin_region"],
                variety=record["variety"],
                process_method=record["process_method"],
                quality_grade=record["quality_grade"],
                cupping_score=record.get("cupping_score"),
                certifications=record.get("certifications"),
                price_usd_per_kg=record["price_usd_per_kg"],
                price_usd_per_lb=record["price_usd_per_lb"],
                ice_c_price_usd_per_lb=record["ice_c_price_usd_per_lb"],
                differential_usd_per_lb=record["differential_usd_per_lb"],
                market_source=record["market_source"],
            )
            self.db.add(price_record)
            imported_count += 1

        self.db.commit()
        return imported_count

    async def enrich_freight_data(self, shipment_id: int) -> None:
        """Extract freight data from completed shipment.

        Extracts data from a shipment record and adds it to the training dataset.

        Args:
            shipment_id: ID of completed shipment
        """
        from app.models.shipment import Shipment

        # High season months for Peru coffee (April-August)
        HIGH_SEASON_MONTHS = [4, 5, 6, 7, 8]

        shipment = self.db.query(Shipment).get(shipment_id)
        if not shipment:
            return

        # Only extract from completed shipments
        if shipment.status != "delivered":
            return

        def _parse_dt(value: str | datetime | None) -> datetime | None:
            if isinstance(value, datetime):
                return value
            if isinstance(value, str):
                try:
                    return datetime.fromisoformat(value)
                except ValueError:
                    return None
            return None

        arrival_raw = getattr(shipment, "arrival_date", None)
        if arrival_raw is None:
            arrival_raw = getattr(shipment, "actual_arrival", None) or getattr(
                shipment, "estimated_arrival", None
            )
        departure_raw = getattr(shipment, "departure_date", None)
        arrival_dt = _parse_dt(arrival_raw)
        departure_dt = _parse_dt(departure_raw)
        freight_cost_usd = getattr(shipment, "freight_cost_usd", None)
        carrier = getattr(shipment, "carrier", None)

        # Create FreightHistory record from shipment data
        if (
            shipment.origin_port
            and shipment.destination_port
            and freight_cost_usd is not None
            and arrival_dt
            and departure_dt
        ):
            freight = FreightHistory(
                route=f"{shipment.origin_port}-{shipment.destination_port}",
                origin_port=shipment.origin_port,
                destination_port=shipment.destination_port,
                carrier=carrier or "Unknown",
                container_type=shipment.container_type or "20ft",
                weight_kg=shipment.weight_kg or 0,
                freight_cost_usd=freight_cost_usd,
                transit_days=(arrival_dt - departure_dt).days,
                departure_date=departure_dt.date(),
                arrival_date=arrival_dt.date(),
                season=("high" if departure_dt.month in HIGH_SEASON_MONTHS else "low"),
            )
            self.db.add(freight)
            self.db.commit()

    async def enrich_price_data(self, deal_id: int) -> None:
        """Extract price data from completed deal.

        Extracts data from a deal record and adds it to the training dataset.

        Args:
            deal_id: ID of completed deal
        """
        from app.models.deal import Deal

        deal = self.db.query(Deal).get(deal_id)
        if not deal:
            return

        # Only extract from closed deals
        if deal.status != "closed":
            return

        # Get current ICE C price for differential calculation
        from app.models.market import MarketObservation

        ice_price_obs = (
            self.db.query(MarketObservation)
            .filter(MarketObservation.key == "COFFEE_C:USD_LB")
            .order_by(MarketObservation.observed_at.desc())
            .first()
        )
        ice_price = ice_price_obs.value if ice_price_obs else 2.0

        # Create CoffeePriceHistory record from deal data
        if deal.price_per_kg and deal.cooperative:
            price_usd_per_kg = deal.price_per_kg
            price_usd_per_lb = price_usd_per_kg * 0.453592  # kg to lb
            differential = price_usd_per_lb - ice_price

            price_record = CoffeePriceHistory(
                date=deal.closed_at or deal.created_at,
                origin_country="Peru",
                origin_region=deal.cooperative.region or "Unknown",
                variety=deal.variety or "Unknown",
                process_method=deal.process_method or "Unknown",
                quality_grade=deal.quality_grade or "Unknown",
                cupping_score=deal.cupping_score,
                certifications=deal.certifications,
                price_usd_per_kg=price_usd_per_kg,
                price_usd_per_lb=price_usd_per_lb,
                ice_c_price_usd_per_lb=ice_price,
                differential_usd_per_lb=differential,
                market_source=f"Deal #{deal_id}",
            )
            self.db.add(price_record)
            self.db.commit()
