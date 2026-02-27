from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.cooperative import Cooperative
from app.models.evidence import EntityEvidence
from app.models.roaster import Roaster
from app.models.source import Source
from app.providers.perplexity import PerplexityClient, PerplexityError, safe_json_loads
from app.services.country_config import get_country_config


def _cooperative_response_format() -> dict[str, Any]:
    schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "entities": {
                "type": "array",
                "maxItems": 20,
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "country": {"type": ["string", "null"]},
                        "region": {"type": ["string", "null"]},
                        "website": {"type": ["string", "null"]},
                        "contact_email": {"type": ["string", "null"]},
                        "notes": {"type": ["string", "null"]},
                        "evidence_urls": {"type": "array", "items": {"type": "string"}},
                        # Basis-Felder
                        "altitude_min_m": {"type": ["number", "null"]},
                        "altitude_max_m": {"type": ["number", "null"]},
                        "varieties": {"type": ["string", "null"]},
                        "certifications": {"type": ["string", "null"]},
                        "processing_methods": {"type": ["string", "null"]},
                        "founding_year": {"type": ["number", "null"]},
                        # Operational Data
                        "farmer_count": {"type": ["number", "null"]},
                        "total_hectares": {"type": ["number", "null"]},
                        "annual_production_kg": {"type": ["number", "null"]},
                        "storage_capacity_kg": {"type": ["number", "null"]},
                        "has_dry_mill": {"type": ["boolean", "null"]},
                        "has_wet_mill": {"type": ["boolean", "null"]},
                        "has_cupping_lab": {"type": ["boolean", "null"]},
                        "processing_facilities": {"type": ["string", "null"]},
                        "years_exporting": {"type": ["number", "null"]},
                        "main_export_destinations": {"type": ["string", "null"]},
                        # Export Readiness
                        "has_export_license": {"type": ["boolean", "null"]},
                        "senasa_registered": {"type": ["boolean", "null"]},
                        "phytosanitary_cert": {"type": ["boolean", "null"]},
                        "customs_broker": {"type": ["string", "null"]},
                        "document_coordinator": {"type": ["string", "null"]},
                        "incoterms_experience": {"type": ["string", "null"]},
                        "minimum_order_kg": {"type": ["number", "null"]},
                        "lead_time_days": {"type": ["number", "null"]},
                        "container_experience": {"type": ["boolean", "null"]},
                        "last_export_year": {"type": ["number", "null"]},
                        # Financial Data
                        "annual_revenue_usd": {"type": ["number", "null"]},
                        "export_volume_kg": {"type": ["number", "null"]},
                        "fob_price_per_kg": {"type": ["number", "null"]},
                        "premium_over_cmarket_pct": {"type": ["number", "null"]},
                        "payment_terms": {"type": ["string", "null"]},
                        "bank_name": {"type": ["string", "null"]},
                        "accepts_letter_of_credit": {"type": ["boolean", "null"]},
                        # Quality
                        "cupping_score_avg": {"type": ["number", "null"]},
                        "cupping_score_range": {"type": ["string", "null"]},
                        "cup_profile_notes": {"type": ["string", "null"]},
                        "defect_rate_pct": {"type": ["number", "null"]},
                        "moisture_content_pct": {"type": ["number", "null"]},
                        "screen_size": {"type": ["string", "null"]},
                        "sca_member": {"type": ["boolean", "null"]},
                        "quality_control_process": {"type": ["string", "null"]},
                        "sample_availability": {"type": ["boolean", "null"]},
                        # Social Impact
                        "female_farmer_pct": {"type": ["number", "null"]},
                        "youth_programs": {"type": ["boolean", "null"]},
                        "education_programs": {"type": ["string", "null"]},
                        "health_programs": {"type": ["string", "null"]},
                        "environmental_programs": {"type": ["string", "null"]},
                        "community_projects": {"type": ["string", "null"]},
                        "fair_trade_premium_use": {"type": ["string", "null"]},
                        # Digital / Communication
                        "social_media_facebook": {"type": ["string", "null"]},
                        "social_media_instagram": {"type": ["string", "null"]},
                        "social_media_linkedin": {"type": ["string", "null"]},
                        "youtube_channel": {"type": ["string", "null"]},
                        "has_online_shop": {"type": ["boolean", "null"]},
                        "languages_spoken": {"type": ["string", "null"]},
                        "contact_phone": {"type": ["string", "null"]},
                        "contact_person": {"type": ["string", "null"]},
                        "contact_role": {"type": ["string", "null"]},
                        # Logistics
                        "nearest_port": {"type": ["string", "null"]},
                        "transport_to_port_hours": {"type": ["number", "null"]},
                        "warehouse_location": {"type": ["string", "null"]},
                        "cold_storage_available": {"type": ["boolean", "null"]},
                    },
                    "required": ["name", "evidence_urls"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["entities"],
        "additionalProperties": False,
    }
    return {"type": "json_schema", "json_schema": {"schema": schema}}


def _roaster_response_format() -> dict[str, Any]:
    schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "entities": {
                "type": "array",
                "maxItems": 20,
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "country": {"type": ["string", "null"]},
                        "city": {"type": ["string", "null"]},
                        "website": {"type": ["string", "null"]},
                        "contact_email": {"type": ["string", "null"]},
                        "notes": {"type": ["string", "null"]},
                        "evidence_urls": {"type": "array", "items": {"type": "string"}},
                        # Classification
                        "peru_focus": {"type": ["boolean", "null"]},
                        "specialty_focus": {"type": ["boolean", "null"]},
                        "price_position": {"type": ["string", "null"]},
                        "direct_trade": {"type": ["boolean", "null"]},
                        "single_origin_focus": {"type": ["boolean", "null"]},
                        "third_wave": {"type": ["boolean", "null"]},
                        # Business Details
                        "founding_year": {"type": ["number", "null"]},
                        "employees_count": {"type": ["number", "null"]},
                        "annual_volume_kg": {"type": ["number", "null"]},
                        "roasting_capacity_kg_day": {"type": ["number", "null"]},
                        "roaster_brand": {"type": ["string", "null"]},
                        "roasting_style": {"type": ["string", "null"]},
                        # Sourcing
                        "origin_countries": {"type": ["string", "null"]},
                        "buys_from_peru": {"type": ["boolean", "null"]},
                        "peru_regions_sourced": {"type": ["string", "null"]},
                        "green_coffee_suppliers": {"type": ["string", "null"]},
                        "buys_direct": {"type": ["boolean", "null"]},
                        "annual_green_purchase_kg": {"type": ["number", "null"]},
                        "preferred_certifications": {"type": ["string", "null"]},
                        "preferred_processing": {"type": ["string", "null"]},
                        "cupping_score_minimum": {"type": ["number", "null"]},
                        # Sales & Distribution
                        "has_cafe": {"type": ["boolean", "null"]},
                        "cafe_count": {"type": ["number", "null"]},
                        "has_online_shop": {"type": ["boolean", "null"]},
                        "sells_wholesale": {"type": ["boolean", "null"]},
                        "sells_subscriptions": {"type": ["boolean", "null"]},
                        "distribution_channels": {"type": ["string", "null"]},
                        # Digital & Contact
                        "social_media_instagram": {"type": ["string", "null"]},
                        "social_media_facebook": {"type": ["string", "null"]},
                        "social_media_linkedin": {"type": ["string", "null"]},
                        "contact_phone": {"type": ["string", "null"]},
                        "contact_person": {"type": ["string", "null"]},
                        "contact_role": {"type": ["string", "null"]},
                        "languages_spoken": {"type": ["string", "null"]},
                        # Sustainability
                        "sustainability_commitment": {"type": ["string", "null"]},
                        "co2_neutral": {"type": ["boolean", "null"]},
                        "packaging_sustainable": {"type": ["boolean", "null"]},
                        "transparency_reports": {"type": ["boolean", "null"]},
                    },
                    "required": ["name", "evidence_urls"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["entities"],
        "additionalProperties": False,
    }
    return {"type": "json_schema", "json_schema": {"schema": schema}}


def _merge_json(existing: dict | None, new: dict) -> dict:
    """Merge new data into existing, never overwrite non-null with null."""
    merged = dict(existing or {})
    for k, v in new.items():
        if v is not None and (k not in merged or merged[k] is None):
            merged[k] = v
    return merged


def _repair_json_with_llm(
    client: PerplexityClient, raw: str, entity_type: str
) -> dict[str, Any]:
    system = (
        "Du bist ein JSON-Repair-Bot. Du bekommst fehlerhaften JSON-Text und gibst NUR valides JSON zurück. "
        "Keine Erklärungen, kein Markdown. Verwende doppelte Anführungszeichen. "
        "Wenn Inhalte fehlen oder abgeschnitten sind, entferne die kaputten Teile statt zu raten. "
        "Output MUSS strikt parsebar sein und genau ein JSON-Objekt enthalten."
    )
    response_format = (
        _cooperative_response_format()
        if entity_type == "cooperative"
        else _roaster_response_format()
    )
    content = client.chat_completions(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": raw[:12000]},
        ],
        temperature=0.0,
        max_tokens=3500,
        response_format=response_format,
    )
    data = safe_json_loads(content)
    if not isinstance(data, dict):
        raise ValueError("JSON repair returned non-object")
    return data


def _norm_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.strip().lower())


def _get_or_create_source(
    db: Session,
    name: str,
    url: str | None,
    kind: str = "api",
    reliability: float | None = 0.6,
) -> Source:
    stmt = select(Source).where(func.lower(Source.name) == name.lower())
    src = db.scalar(stmt)
    if src:
        return src
    src = Source(name=name, url=url, kind=kind, reliability=reliability)
    db.add(src)
    db.commit()
    db.refresh(src)
    return src


COOP_QUERIES = [
    "Peru coffee cooperative exporter list",
    "cooperativa cafetalera peru exportadora",
    "cooperativa cafe peru fairtrade organic",
    "central de cooperativas café Perú exportación",
    "Peru coffee cooperative Cajamarca",
    "Peru coffee cooperative Junin Satipo",
    "Peru coffee cooperative Puno Sandia",
    "Peru coffee cooperative San Martin Moyobamba",
    "Peru coffee cooperative Amazonas Chachapoyas",
    "Peru coffee cooperative Cusco Quillabamba",
    "cooperativa cafe peru cupping score specialty",
    "Peru specialty coffee producer exporter FOB price",
    "cooperativa agraria cafetalera peru organic fair trade export",
]

ROASTER_QUERIES = [
    "specialty coffee roaster Germany",
    "Kaffeerösterei Deutschland specialty direct trade",
    "Third Wave coffee roastery Deutschland",
    "Rösterei Berlin specialty coffee",
    "Rösterei München specialty coffee",
    "Rösterei Hamburg specialty coffee",
    "Rösterei Köln Düsseldorf specialty coffee",
    "Rösterei Stuttgart Frankfurt specialty coffee",
    "Rösterei Leipzig Dresden specialty coffee",
    "German specialty roaster Peru single origin",
    "Kaffeerösterei direct trade Peru Deutschland",
    "best specialty coffee roasters Germany 2024 2025",
]


def _extract_entities_with_llm(
    client: PerplexityClient,
    *,
    entity_type: str,
    search_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if entity_type == "cooperative":
        system = (
            "Du extrahierst MAXIMAL detaillierte Informationen über peruanische Kaffee-Kooperativen aus Suchergebnissen. "
            "Extrahiere JEDES Detail, das Du findest: Höhenlage, Sorten, Zertifizierungen, Mitgliederzahl, Exportmengen, "
            "Cupping-Scores, Kontaktdaten, Social Media, Verarbeitungsmethoden, Lagerkapazitäten, Finanzinformationen, "
            "Export-Lizenzen, SENASA-Registrierung, Zahlungsbedingungen, soziale Programme, Frauenanteil etc. "
            "NICHTS auslassen was verfügbar ist. Unbekannt => null. "
            "Gib NUR valides JSON zurück (kein Markdown, keine Erklärungen). "
            "Regeln: (1) nichts erfinden; (2) nur echte Kooperativen; (3) Duplikate entfernen; "
            "(4) evidence_urls nur aus gelieferten URLs; (5) max 20 entities."
        )
    else:
        system = (
            "Du extrahierst MAXIMAL detaillierte Informationen über deutsche Specialty-Kaffeeröstereien aus Suchergebnissen. "
            "Extrahiere JEDES Detail: Stadt, Peru-Fokus, Preispositionierung (low/mid/premium/ultra-premium), Röststil, "
            "Kapazität, Vertriebskanäle, ob sie Direct Trade machen, welche Herkunftsländer, Anzahl Cafés, Online-Shop, "
            "Social Media, Kontaktdaten, Nachhaltigkeits-Commitment, Röstmaschinen-Marke, Gründungsjahr, Mitarbeiteranzahl etc. "
            "NICHTS auslassen was verfügbar ist. Unbekannt => null. "
            "Gib NUR valides JSON zurück (kein Markdown, keine Erklärungen). "
            "Regeln: (1) nichts erfinden; (2) nur echte Röstereien; (3) Duplikate entfernen; "
            "(4) evidence_urls nur aus gelieferten URLs; (5) max 20 entities."
        )

    user = {"entity_type": entity_type, "results": search_results}
    response_format = (
        _cooperative_response_format()
        if entity_type == "cooperative"
        else _roaster_response_format()
    )
    content = client.chat_completions(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
        ],
        temperature=0.0,
        max_tokens=4000,
        response_format=response_format,
    )
    try:
        data = safe_json_loads(content)
    except Exception:
        data = _repair_json_with_llm(client, content, entity_type)

    ents = data.get("entities") or []
    if not isinstance(ents, list):
        return []

    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for ent in ents:
        if not isinstance(ent, dict):
            continue
        name = (ent.get("name") or "").strip()
        if not name:
            continue
        k = _norm_name(name)
        if k in seen:
            continue
        seen.add(k)
        out.append(ent)
    return out


def seed_discovery(
    db: Session,
    *,
    entity_type: str,
    max_entities: int = 200,
    dry_run: bool = False,
    country_filter: str | None = None,
) -> dict[str, Any]:
    if entity_type not in {"cooperative", "roaster"}:
        raise ValueError("entity_type must be cooperative|roaster")

    src = _get_or_create_source(
        db,
        name="Perplexity Discovery",
        url="https://docs.perplexity.ai/",
        kind="api",
        reliability=0.6,
    )

    default_country = "PE" if entity_type == "cooperative" else "DE"
    country = country_filter or default_country
    country_cfg = get_country_config(country)
    if country_cfg is not None:
        if entity_type == "cooperative":
            queries = country_cfg.discovery_cooperative_queries or COOP_QUERIES
        else:
            queries = country_cfg.discovery_roaster_queries or ROASTER_QUERIES
    else:
        queries = COOP_QUERIES if entity_type == "cooperative" else ROASTER_QUERIES

    created = 0
    updated = 0
    skipped = 0
    errors: list[str] = []

    client = PerplexityClient()
    try:
        aggregated: list[dict[str, Any]] = []
        seen_urls: set[str] = set()

        for q in queries:
            if len(aggregated) >= 120:
                break
            try:
                results = client.search(
                    q, max_results=20, country=country, max_tokens_per_page=512
                )
                for r in results:
                    if r.url in seen_urls:
                        continue
                    seen_urls.add(r.url)
                    aggregated.append(
                        {"title": r.title, "url": r.url, "snippet": r.snippet}
                    )
            except Exception as exc:
                errors.append(f"search failed for '{q}': {exc}")

        entities: list[dict[str, Any]] = []
        chunk_size = 20
        for i in range(0, len(aggregated), chunk_size):
            chunk = aggregated[i : i + chunk_size]
            if not chunk:
                continue
            try:
                ents = _extract_entities_with_llm(
                    client, entity_type=entity_type, search_results=chunk
                )
                entities.extend(ents)
            except Exception as exc:
                errors.append(f"extract failed chunk {i}-{i + chunk_size}: {exc}")

        deduped: dict[str, dict[str, Any]] = {}
        for ent in entities:
            k = _norm_name(ent["name"])
            if not k:
                continue
            if k not in deduped:
                deduped[k] = ent
            else:
                deduped[k]["evidence_urls"] = list(
                    {
                        *(deduped[k].get("evidence_urls") or []),
                        *(ent.get("evidence_urls") or []),
                    }
                )

        now = datetime.utcnow()

        for ent in list(deduped.values())[:max_entities]:
            name = ent["name"].strip()
            entity_id: int | None = None

            if entity_type == "cooperative":
                stmt_coop = select(Cooperative).where(
                    func.lower(Cooperative.name) == name.lower()
                )
                coop = db.scalar(stmt_coop)
                is_new = coop is None
                if coop is None:
                    coop = Cooperative(
                        name=name, status="active", next_action="In Recherche"
                    )
                    db.add(coop)

                # Basic fields
                if ent.get("region") and not coop.region:
                    coop.region = str(ent["region"])[:255]
                if ent.get("website") and not coop.website:
                    coop.website = str(ent["website"])[:500]
                if ent.get("contact_email") and not coop.contact_email:
                    coop.contact_email = str(ent["contact_email"])[:320]
                if ent.get("varieties") and not coop.varieties:
                    coop.varieties = str(ent["varieties"])[:255]
                if ent.get("certifications") and not coop.certifications:
                    coop.certifications = str(ent["certifications"])[:255]

                # altitude_m from altitude_min_m or altitude_max_m
                if not coop.altitude_m:
                    alt_min = ent.get("altitude_min_m")
                    alt_max = ent.get("altitude_max_m")
                    if alt_min is not None and alt_max is not None:
                        coop.altitude_m = (float(alt_min) + float(alt_max)) / 2
                    elif alt_min is not None:
                        coop.altitude_m = float(alt_min)
                    elif alt_max is not None:
                        coop.altitude_m = float(alt_max)

                # Notes
                if ent.get("notes"):
                    coop.notes = (coop.notes or "").strip()
                    add = str(ent["notes"]).strip()
                    if add and add not in (coop.notes or ""):
                        coop.notes = (
                            (coop.notes + "\n\n" + add).strip() if coop.notes else add
                        )

                # Operational Data JSON
                operational_data_new = {
                    k: ent.get(k)
                    for k in [
                        "farmer_count",
                        "total_hectares",
                        "annual_production_kg",
                        "storage_capacity_kg",
                        "has_dry_mill",
                        "has_wet_mill",
                        "has_cupping_lab",
                        "processing_facilities",
                        "years_exporting",
                        "main_export_destinations",
                        "founding_year",
                        "processing_methods",
                    ]
                    if ent.get(k) is not None
                }
                if operational_data_new:
                    coop.operational_data = _merge_json(
                        coop.operational_data, operational_data_new
                    )

                # Export Readiness JSON
                export_readiness_new = {
                    k: ent.get(k)
                    for k in [
                        "has_export_license",
                        "senasa_registered",
                        "phytosanitary_cert",
                        "customs_broker",
                        "document_coordinator",
                        "incoterms_experience",
                        "minimum_order_kg",
                        "lead_time_days",
                        "container_experience",
                        "last_export_year",
                    ]
                    if ent.get(k) is not None
                }
                if export_readiness_new:
                    coop.export_readiness = _merge_json(
                        coop.export_readiness, export_readiness_new
                    )

                # Financial Data JSON
                financial_data_new = {
                    k: ent.get(k)
                    for k in [
                        "annual_revenue_usd",
                        "export_volume_kg",
                        "fob_price_per_kg",
                        "premium_over_cmarket_pct",
                        "payment_terms",
                        "bank_name",
                        "accepts_letter_of_credit",
                    ]
                    if ent.get(k) is not None
                }
                if financial_data_new:
                    coop.financial_data = _merge_json(
                        coop.financial_data, financial_data_new
                    )

                # Social Impact Data JSON
                social_impact_data_new = {
                    k: ent.get(k)
                    for k in [
                        "female_farmer_pct",
                        "youth_programs",
                        "education_programs",
                        "health_programs",
                        "environmental_programs",
                        "community_projects",
                        "fair_trade_premium_use",
                    ]
                    if ent.get(k) is not None
                }
                if social_impact_data_new:
                    coop.social_impact_data = _merge_json(
                        coop.social_impact_data, social_impact_data_new
                    )

                # Digital Footprint JSON
                digital_footprint_new = {
                    k: ent.get(k)
                    for k in [
                        "social_media_facebook",
                        "social_media_instagram",
                        "social_media_linkedin",
                        "youtube_channel",
                        "has_online_shop",
                        "languages_spoken",
                        "contact_phone",
                        "contact_person",
                        "contact_role",
                    ]
                    if ent.get(k) is not None
                }
                if digital_footprint_new:
                    coop.digital_footprint = _merge_json(
                        coop.digital_footprint, digital_footprint_new
                    )

                # Meta fields
                coop.meta = coop.meta or {}
                coop.meta.setdefault("discovery", {})
                coop.meta["discovery"].update(
                    {"provider": "perplexity", "last_run": now.isoformat()}
                )

                # Quality data in meta["quality"]
                quality_new = {
                    k: ent.get(k)
                    for k in [
                        "cupping_score_avg",
                        "cupping_score_range",
                        "cup_profile_notes",
                        "defect_rate_pct",
                        "moisture_content_pct",
                        "screen_size",
                        "sca_member",
                        "quality_control_process",
                        "sample_availability",
                    ]
                    if ent.get(k) is not None
                }
                if quality_new:
                    coop.meta.setdefault("quality", {})
                    coop.meta["quality"] = _merge_json(
                        coop.meta.get("quality"), quality_new
                    )

                # Logistics data in meta["logistics"]
                logistics_new = {
                    k: ent.get(k)
                    for k in [
                        "nearest_port",
                        "transport_to_port_hours",
                        "warehouse_location",
                        "cold_storage_available",
                    ]
                    if ent.get(k) is not None
                }
                if logistics_new:
                    coop.meta.setdefault("logistics", {})
                    coop.meta["logistics"] = _merge_json(
                        coop.meta.get("logistics"), logistics_new
                    )

                if not dry_run:
                    db.commit()
                    db.refresh(coop)
                    entity_id = coop.id

            else:
                stmt_roaster = select(Roaster).where(
                    func.lower(Roaster.name) == name.lower()
                )
                roaster = db.scalar(stmt_roaster)
                is_new = roaster is None
                if roaster is None:
                    roaster = Roaster(
                        name=name, status="active", next_action="In Recherche"
                    )
                    db.add(roaster)

                # Basic fields
                if ent.get("city") and not roaster.city:
                    roaster.city = str(ent["city"])[:255]
                if ent.get("website") and not roaster.website:
                    roaster.website = str(ent["website"])[:500]
                if ent.get("contact_email") and not roaster.contact_email:
                    roaster.contact_email = str(ent["contact_email"])[:320]

                # Classification fields
                if ent.get("peru_focus") is not None and not roaster.peru_focus:
                    roaster.peru_focus = bool(ent["peru_focus"])
                elif ent.get("buys_from_peru") is not None and not roaster.peru_focus:
                    roaster.peru_focus = bool(ent["buys_from_peru"])

                if ent.get("specialty_focus") is not None:
                    roaster.specialty_focus = bool(ent["specialty_focus"])
                elif ent.get("third_wave") is not None:
                    roaster.specialty_focus = bool(ent["third_wave"])

                if ent.get("price_position") and not roaster.price_position:
                    roaster.price_position = str(ent["price_position"])[:64]

                # Notes
                if ent.get("notes"):
                    roaster.notes = (roaster.notes or "").strip()
                    add = str(ent["notes"]).strip()
                    if add and add not in (roaster.notes or ""):
                        roaster.notes = (
                            (roaster.notes + "\n\n" + add).strip()
                            if roaster.notes
                            else add
                        )

                # Meta fields
                roaster.meta = roaster.meta or {}
                roaster.meta.setdefault("discovery", {})
                roaster.meta["discovery"].update(
                    {"provider": "perplexity", "last_run": now.isoformat()}
                )

                # Sourcing data in meta["sourcing"]
                sourcing_new = {
                    k: ent.get(k)
                    for k in [
                        "origin_countries",
                        "peru_regions_sourced",
                        "green_coffee_suppliers",
                        "buys_direct",
                        "annual_green_purchase_kg",
                        "preferred_certifications",
                        "preferred_processing",
                        "cupping_score_minimum",
                    ]
                    if ent.get(k) is not None
                }
                if sourcing_new:
                    roaster.meta.setdefault("sourcing", {})
                    roaster.meta["sourcing"] = _merge_json(
                        roaster.meta.get("sourcing"), sourcing_new
                    )

                # Business data in meta["business"]
                business_new = {
                    k: ent.get(k)
                    for k in [
                        "founding_year",
                        "employees_count",
                        "annual_volume_kg",
                        "roasting_capacity_kg_day",
                        "roaster_brand",
                        "roasting_style",
                        "direct_trade",
                        "single_origin_focus",
                    ]
                    if ent.get(k) is not None
                }
                if business_new:
                    roaster.meta.setdefault("business", {})
                    roaster.meta["business"] = _merge_json(
                        roaster.meta.get("business"), business_new
                    )

                # Sales data in meta["sales"]
                sales_new = {
                    k: ent.get(k)
                    for k in [
                        "has_cafe",
                        "cafe_count",
                        "has_online_shop",
                        "sells_wholesale",
                        "sells_subscriptions",
                        "distribution_channels",
                    ]
                    if ent.get(k) is not None
                }
                if sales_new:
                    roaster.meta.setdefault("sales", {})
                    roaster.meta["sales"] = _merge_json(
                        roaster.meta.get("sales"), sales_new
                    )

                # Digital data in meta["digital"]
                digital_new = {
                    k: ent.get(k)
                    for k in [
                        "social_media_instagram",
                        "social_media_facebook",
                        "social_media_linkedin",
                        "contact_phone",
                        "contact_person",
                        "contact_role",
                        "languages_spoken",
                    ]
                    if ent.get(k) is not None
                }
                if digital_new:
                    roaster.meta.setdefault("digital", {})
                    roaster.meta["digital"] = _merge_json(
                        roaster.meta.get("digital"), digital_new
                    )

                # Sustainability data in meta["sustainability"]
                sustainability_new = {
                    k: ent.get(k)
                    for k in [
                        "sustainability_commitment",
                        "co2_neutral",
                        "packaging_sustainable",
                        "transparency_reports",
                    ]
                    if ent.get(k) is not None
                }
                if sustainability_new:
                    roaster.meta.setdefault("sustainability", {})
                    roaster.meta["sustainability"] = _merge_json(
                        roaster.meta.get("sustainability"), sustainability_new
                    )

                if not dry_run:
                    db.commit()
                    db.refresh(roaster)
                    entity_id = roaster.id

            ev_urls = list(dict.fromkeys((ent.get("evidence_urls") or [])))

            if ev_urls and (not dry_run) and entity_id is not None:
                for u in ev_urls[:10]:
                    try:
                        ev = EntityEvidence(
                            entity_type=entity_type,
                            entity_id=entity_id,
                            source_id=src.id,
                            evidence_url=u,
                            extracted_at=now,
                            meta={"provider": "perplexity"},
                        )
                        db.add(ev)
                        db.commit()
                    except Exception:
                        db.rollback()

            if is_new:
                created += 1
            else:
                updated += 1

        if dry_run:
            db.rollback()

    except PerplexityError as exc:
        errors.append(str(exc))
    finally:
        client.close()

    return {
        "entity_type": entity_type,
        "country": country,
        "dry_run": dry_run,
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
    }
