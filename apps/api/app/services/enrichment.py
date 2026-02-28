from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse
import ipaddress
import socket

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.models.cooperative import Cooperative
from app.models.roaster import Roaster
from app.models.web_extract import WebExtract
from app.models.entity_event import EntityEvent
from app.providers.perplexity import PerplexityClient, safe_json_loads


def _clean_text(txt: str) -> str:
    return re.sub(r"\s+", " ", txt or "").strip()


def _sha256(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8", errors="ignore")).hexdigest()


def _domain(url: str) -> str | None:
    try:
        return urlparse(url).netloc.lower() or None
    except Exception:
        return None


def _normalize_url(u: str) -> str:
    u = (u or "").strip()
    if not u:
        return u
    if not re.match(r"^https?://", u, flags=re.I):
        u = "https://" + u.lstrip("/")
    return u


def _split_csv(value: str | None) -> list[str]:
    return [v.strip() for v in (value or "").split(",") if v.strip()]


def _is_allowed_host(hostname: str) -> bool:
    """
    Return True if the given hostname is allowed for outbound HTTP requests.

    This uses an application-level allowlist to prevent the service from
    becoming an arbitrary HTTP proxy (full SSRF). The allowlist is expected
    to be configured via settings, for example as a list of hostnames or
    domain suffixes.
    """
    if not hostname:
        return False

    # Built-in, conservative defaults for hosts this service is expected to call.
    # These are combined with any project-specific allowlist from settings.
    builtin_allowed = [
        "coffee.studio",
        "www.coffee.studio",
        "www.coffeestudio.app",
    ]
    configured_hosts = _split_csv(getattr(settings, "ENRICH_ALLOWED_HOSTS", None))
    configured_domains = _split_csv(getattr(settings, "ENRICH_ALLOWED_DOMAINS", None))

    # Combine built-in allowlist with any configured values, removing empties.
    allowed = [
        h for h in (builtin_allowed + configured_hosts + configured_domains) if h
    ]
    if not allowed:
        # With an empty combined allowlist, deny by default to avoid SSRF.
        return False

    hostname = hostname.lower()
    for pattern in allowed:
        pattern = (pattern or "").lower().strip()
        if not pattern:
            continue
        if pattern.startswith("."):
            # Suffix match for subdomains, allow patterns like ".example.com"
            if hostname.endswith(pattern):
                return True
            continue

        # Exact match
        if hostname == pattern:
            return True
        # Allow suffix matches for domains provided without leading dot.
        if hostname.endswith("." + pattern):
            return True
    return False


def _validate_public_http_url(url: str) -> str:
    """
    Normalize and validate that the URL uses http(s), that the hostname is
    allowed, and that it does not resolve to localhost or private/internal IP
    address ranges. Raises ValueError on failure.
    """
    normalized = _normalize_url(url)
    if not normalized:
        raise ValueError("empty url")

    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("unsupported URL scheme")
    if not parsed.hostname:
        raise ValueError("invalid URL: missing host")

    hostname = parsed.hostname.lower()
    if not _is_allowed_host(hostname):
        raise ValueError("URL host is not allowed")

    # Optionally restrict ports to typical HTTP(S) ports. If no port is given,
    # httpx will use defaults based on the scheme.
    if parsed.port is not None and parsed.port not in (80, 443):
        raise ValueError("unsupported URL port")

    try:
        addrinfo_list = socket.getaddrinfo(parsed.hostname, None)
    except OSError:
        raise ValueError("unable to resolve host")

    for family, _, _, _, sockaddr in addrinfo_list:
        ip_str = None
        if family == socket.AF_INET:
            ip_str = sockaddr[0]
        elif family == socket.AF_INET6:
            ip_str = sockaddr[0]
        if not ip_str:
            continue
        ip = ipaddress.ip_address(ip_str)
        if (
            ip.is_loopback
            or ip.is_private
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise ValueError("URL host resolves to a disallowed IP address")

    return normalized


def fetch_text(url: str, timeout_seconds: int = 25) -> tuple[str, dict[str, Any]]:
    # Validate the initial URL before making any request.
    current_url = _validate_public_http_url(url)
    headers = {
        # browser-like UA reduces dumb 403s (not all)
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36 CoffeeStudio/0.3",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    }
    max_redirects = 5
    with httpx.Client(
        timeout=timeout_seconds, follow_redirects=False, headers=headers
    ) as client:
        redirects_followed = 0
        while True:
            r = client.get(current_url)
            # If this is not a redirect, stop here.
            if r.status_code not in {301, 302, 303, 307, 308}:
                break

            location = r.headers.get("location")
            if not location:
                break

            # Resolve relative redirects against the current URL.
            try:
                next_url = str(httpx.URL(current_url).join(location))
            except Exception:
                raise ValueError("invalid redirect URL")

            # Validate each redirect target to prevent SSRF via redirects.
            current_url = _validate_public_http_url(next_url)
            redirects_followed += 1
            if redirects_followed > max_redirects:
                raise ValueError("too many redirects")

        r.raise_for_status()
        html = r.text

    # Re-validate the final URL after following redirects to ensure that
    # redirection did not lead to an internal or otherwise disallowed host.
    final_url_str = str(r.url)
    safe_final_url = _validate_public_http_url(final_url_str)

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = _clean_text(soup.get_text(" "))
    meta = {
        "final_url": safe_final_url,
        "status_code": r.status_code,
        "content_type": r.headers.get("content-type"),
        "domain": _domain(safe_final_url),
    }
    return text[:20000], meta


def _merge_json(existing: dict | None, new: dict) -> dict:
    """Merge new data into existing, never overwrite non-null with null."""
    merged = dict(existing or {})
    for k, v in new.items():
        if v is not None and (k not in merged or merged[k] is None):
            merged[k] = v
    return merged


def _cooperative_enrichment_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "region": {"type": ["string", "null"]},
            "city": {"type": ["string", "null"]},
            "varieties": {"type": ["string", "null"]},
            "certifications": {"type": ["string", "null"]},
            "contact_email": {"type": ["string", "null"]},
            "website": {"type": ["string", "null"]},
            "summary_de": {"type": ["string", "null"]},
            # Basis-Felder
            "altitude_min_m": {"type": ["number", "null"]},
            "altitude_max_m": {"type": ["number", "null"]},
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
        "required": [],
        "additionalProperties": False,
    }


def _roaster_enrichment_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "city": {"type": ["string", "null"]},
            "contact_email": {"type": ["string", "null"]},
            "website": {"type": ["string", "null"]},
            "summary_de": {"type": ["string", "null"]},
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
        "required": [],
        "additionalProperties": False,
    }


def _extract_structured_with_llm(
    client: PerplexityClient, *, entity_type: str, text: str
) -> dict[str, Any]:
    if entity_type == "cooperative":
        schema = _cooperative_enrichment_schema()
        system = (
            "Du extrahierst MAXIMAL detaillierte strukturierte Informationen über eine peruanische Kaffee-Kooperative aus einem Webseiten-Text. "
            "Extrahiere JEDES Detail, das Du findest: Höhenlage, Sorten, Zertifizierungen, Mitgliederzahl, Exportmengen, "
            "Cupping-Scores, Kontaktdaten, Social Media, Verarbeitungsmethoden, Lagerkapazitäten, Finanzinformationen, "
            "Export-Lizenzen, SENASA-Registrierung, Zahlungsbedingungen, soziale Programme, Frauenanteil, Logistik etc. "
            "NICHTS auslassen was verfügbar ist. Gib NUR valides JSON zurück (kein Markdown). "
            "Nichts erfinden. Unbekannt => null. Wenn der Text nicht passt: alles null."
        )
    else:
        schema = _roaster_enrichment_schema()
        system = (
            "Du extrahierst MAXIMAL detaillierte strukturierte Informationen über eine deutsche Specialty-Kaffeerösterei aus einem Webseiten-Text. "
            "Extrahiere JEDES Detail: Stadt, Peru-Fokus, Preispositionierung (low/mid/premium/ultra-premium), Röststil, "
            "Kapazität, Vertriebskanäle, ob sie Direct Trade machen, welche Herkunftsländer, Anzahl Cafés, Online-Shop, "
            "Social Media, Kontaktdaten, Nachhaltigkeits-Commitment, Röstmaschinen-Marke, Gründungsjahr, Mitarbeiteranzahl etc. "
            "NICHTS auslassen was verfügbar ist. Gib NUR valides JSON zurück (kein Markdown). "
            "Nichts erfinden. Unbekannt => null. Wenn der Text nicht passt: alles null."
        )
    content = client.chat_completions(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": text[:12000]},
        ],
        temperature=0.0,
        max_tokens=2500,
        response_format={"type": "json_schema", "json_schema": {"schema": schema}},
    )
    data = safe_json_loads(content)
    return data if isinstance(data, dict) else {}


def enrich_entity(
    db: Session,
    *,
    entity_type: str,
    entity_id: int,
    url: str | None = None,
    use_llm: bool = True,
) -> dict[str, Any]:
    if entity_type not in {"cooperative", "roaster"}:
        raise ValueError("entity_type must be cooperative|roaster")

    entity = (
        db.get(Cooperative, entity_id)
        if entity_type == "cooperative"
        else db.get(Roaster, entity_id)
    )
    if not entity:
        raise ValueError("entity not found")

    target_url = _normalize_url(url or getattr(entity, "website", None) or "")
    if not target_url:
        raise ValueError("no url (provide url or set entity.website)")

    now = datetime.now(timezone.utc)

    try:
        text, meta = fetch_text(target_url)
        chash = _sha256(text)
        # meta["final_url"] has already been validated in fetch_text.
        final_url = meta.get("final_url") or target_url

        # IMPORTANT: stmt must be a SQLAlchemy select(), never a plain string
        stmt = select(WebExtract).where(
            WebExtract.entity_type == entity_type,
            WebExtract.entity_id == entity_id,
            WebExtract.url == final_url,
        )
        we = db.scalar(stmt)

        if not we:
            we = WebExtract(entity_type=entity_type, entity_id=entity_id, url=final_url)
            db.add(we)

        we.status = "ok"
        we.retrieved_at = now
        we.content_text = text
        we.content_hash = chash
        we.meta = meta

        extracted: dict[str, Any] = {}
        if use_llm and settings.PERPLEXITY_API_KEY:
            client = PerplexityClient()
            try:
                extracted = _extract_structured_with_llm(
                    client, entity_type=entity_type, text=text
                )
            finally:
                client.close()

        we.extracted_json = extracted or None
        try:
            db.commit()
        except Exception as commit_exc:
            # Handle possible race/unique constraint on web_extracts insert: try to
            # rollback and load existing record instead of failing with 409.
            from sqlalchemy.exc import IntegrityError

            db.rollback()
            if isinstance(commit_exc, IntegrityError) or isinstance(
                commit_exc.__cause__, IntegrityError
            ):
                # Try to fetch the existing web extract created by a concurrent
                # request and continue.
                stmt_retry = select(WebExtract).where(
                    WebExtract.entity_type == entity_type,
                    WebExtract.entity_id == entity_id,
                    WebExtract.url == final_url,
                )
                _ = db.scalar(stmt_retry)
                if we is None:
                    # If still missing, re-raise the original exception.
                    raise
            else:
                raise

        db.refresh(we)

        updated_fields: list[str] = []
        if extracted:
            # Use isinstance checks for proper type narrowing
            if isinstance(entity, Cooperative):
                # Basic fields
                if extracted.get("region") and not entity.region:
                    entity.region = str(extracted["region"])[:255]
                    updated_fields.append("region")
                if extracted.get("varieties") and not entity.varieties:
                    entity.varieties = str(extracted["varieties"])[:255]
                    updated_fields.append("varieties")
                if extracted.get("certifications") and not entity.certifications:
                    entity.certifications = str(extracted["certifications"])[:255]
                    updated_fields.append("certifications")

                # altitude_m from altitude_min_m or altitude_max_m
                if not entity.altitude_m:
                    alt_min = extracted.get("altitude_min_m")
                    alt_max = extracted.get("altitude_max_m")
                    if alt_min is not None and alt_max is not None:
                        entity.altitude_m = (float(alt_min) + float(alt_max)) / 2
                        updated_fields.append("altitude_m")
                    elif alt_min is not None:
                        entity.altitude_m = float(alt_min)
                        updated_fields.append("altitude_m")
                    elif alt_max is not None:
                        entity.altitude_m = float(alt_max)
                        updated_fields.append("altitude_m")

                # Operational Data JSON
                operational_data_new = {
                    k: extracted.get(k)
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
                    if extracted.get(k) is not None
                }
                if operational_data_new:
                    entity.operational_data = _merge_json(
                        entity.operational_data, operational_data_new
                    )
                    updated_fields.append("operational_data")

                # Export Readiness JSON
                export_readiness_new = {
                    k: extracted.get(k)
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
                    if extracted.get(k) is not None
                }
                if export_readiness_new:
                    entity.export_readiness = _merge_json(
                        entity.export_readiness, export_readiness_new
                    )
                    updated_fields.append("export_readiness")

                # Financial Data JSON
                financial_data_new = {
                    k: extracted.get(k)
                    for k in [
                        "annual_revenue_usd",
                        "export_volume_kg",
                        "fob_price_per_kg",
                        "premium_over_cmarket_pct",
                        "payment_terms",
                        "bank_name",
                        "accepts_letter_of_credit",
                    ]
                    if extracted.get(k) is not None
                }
                if financial_data_new:
                    entity.financial_data = _merge_json(
                        entity.financial_data, financial_data_new
                    )
                    updated_fields.append("financial_data")

                # Social Impact Data JSON
                social_impact_data_new = {
                    k: extracted.get(k)
                    for k in [
                        "female_farmer_pct",
                        "youth_programs",
                        "education_programs",
                        "health_programs",
                        "environmental_programs",
                        "community_projects",
                        "fair_trade_premium_use",
                    ]
                    if extracted.get(k) is not None
                }
                if social_impact_data_new:
                    entity.social_impact_data = _merge_json(
                        entity.social_impact_data, social_impact_data_new
                    )
                    updated_fields.append("social_impact_data")

                # Digital Footprint JSON
                digital_footprint_new = {
                    k: extracted.get(k)
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
                    if extracted.get(k) is not None
                }
                if digital_footprint_new:
                    entity.digital_footprint = _merge_json(
                        entity.digital_footprint, digital_footprint_new
                    )
                    updated_fields.append("digital_footprint")

                # Quality data in meta["quality"]
                entity.meta = entity.meta or {}
                quality_new = {
                    k: extracted.get(k)
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
                    if extracted.get(k) is not None
                }
                if quality_new:
                    entity.meta.setdefault("quality", {})
                    entity.meta["quality"] = _merge_json(
                        entity.meta.get("quality"), quality_new
                    )
                    updated_fields.append("meta.quality")

                # Logistics data in meta["logistics"]
                logistics_new = {
                    k: extracted.get(k)
                    for k in [
                        "nearest_port",
                        "transport_to_port_hours",
                        "warehouse_location",
                        "cold_storage_available",
                    ]
                    if extracted.get(k) is not None
                }
                if logistics_new:
                    entity.meta.setdefault("logistics", {})
                    entity.meta["logistics"] = _merge_json(
                        entity.meta.get("logistics"), logistics_new
                    )
                    updated_fields.append("meta.logistics")

            elif isinstance(entity, Roaster):
                # Basic fields
                if extracted.get("city") and not entity.city:
                    entity.city = str(extracted["city"])[:255]
                    updated_fields.append("city")

                # Classification fields
                if extracted.get("peru_focus") is not None and not entity.peru_focus:
                    entity.peru_focus = bool(extracted["peru_focus"])
                    updated_fields.append("peru_focus")
                elif (
                    extracted.get("buys_from_peru") is not None
                    and not entity.peru_focus
                ):
                    entity.peru_focus = bool(extracted["buys_from_peru"])
                    updated_fields.append("peru_focus")

                if extracted.get("specialty_focus") is not None:
                    entity.specialty_focus = bool(extracted["specialty_focus"])
                    updated_fields.append("specialty_focus")
                elif extracted.get("third_wave") is not None:
                    entity.specialty_focus = bool(extracted["third_wave"])
                    updated_fields.append("specialty_focus")

                if extracted.get("price_position") and not entity.price_position:
                    entity.price_position = str(extracted["price_position"])[:64]
                    updated_fields.append("price_position")

                # Meta fields
                entity.meta = entity.meta or {}

                # Sourcing data in meta["sourcing"]
                sourcing_new = {
                    k: extracted.get(k)
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
                    if extracted.get(k) is not None
                }
                if sourcing_new:
                    entity.meta.setdefault("sourcing", {})
                    entity.meta["sourcing"] = _merge_json(
                        entity.meta.get("sourcing"), sourcing_new
                    )
                    updated_fields.append("meta.sourcing")

                # Business data in meta["business"]
                business_new = {
                    k: extracted.get(k)
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
                    if extracted.get(k) is not None
                }
                if business_new:
                    entity.meta.setdefault("business", {})
                    entity.meta["business"] = _merge_json(
                        entity.meta.get("business"), business_new
                    )
                    updated_fields.append("meta.business")

                # Sales data in meta["sales"]
                sales_new = {
                    k: extracted.get(k)
                    for k in [
                        "has_cafe",
                        "cafe_count",
                        "has_online_shop",
                        "sells_wholesale",
                        "sells_subscriptions",
                        "distribution_channels",
                    ]
                    if extracted.get(k) is not None
                }
                if sales_new:
                    entity.meta.setdefault("sales", {})
                    entity.meta["sales"] = _merge_json(
                        entity.meta.get("sales"), sales_new
                    )
                    updated_fields.append("meta.sales")

                # Digital data in meta["digital"]
                digital_new = {
                    k: extracted.get(k)
                    for k in [
                        "social_media_instagram",
                        "social_media_facebook",
                        "social_media_linkedin",
                        "contact_phone",
                        "contact_person",
                        "contact_role",
                        "languages_spoken",
                    ]
                    if extracted.get(k) is not None
                }
                if digital_new:
                    entity.meta.setdefault("digital", {})
                    entity.meta["digital"] = _merge_json(
                        entity.meta.get("digital"), digital_new
                    )
                    updated_fields.append("meta.digital")

                # Sustainability data in meta["sustainability"]
                sustainability_new = {
                    k: extracted.get(k)
                    for k in [
                        "sustainability_commitment",
                        "co2_neutral",
                        "packaging_sustainable",
                        "transparency_reports",
                    ]
                    if extracted.get(k) is not None
                }
                if sustainability_new:
                    entity.meta.setdefault("sustainability", {})
                    entity.meta["sustainability"] = _merge_json(
                        entity.meta.get("sustainability"), sustainability_new
                    )
                    updated_fields.append("meta.sustainability")

            # Common fields for both entity types
            if extracted.get("contact_email") and not entity.contact_email:
                entity.contact_email = str(extracted["contact_email"])[:320]
                updated_fields.append("contact_email")

            if extracted.get("website") and not entity.website:
                entity.website = _normalize_url(str(extracted["website"]))[:500]
                updated_fields.append("website")

            entity.last_verified_at = now
            updated_fields.append("last_verified_at")
            db.add(entity)

        db.add(
            EntityEvent(
                entity_type=entity_type,
                entity_id=entity_id,
                event_type="enriched",
                payload={"url": target_url, "updated_fields": updated_fields},
            )
        )
        db.commit()

        return {
            "status": "ok",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "url": target_url,
            "web_extract_id": we.id,
            "updated_fields": updated_fields,
            "used_llm": bool(use_llm and settings.PERPLEXITY_API_KEY),
        }

    except Exception as e:
        # Record a failed web extract but defend against duplicate inserts.
        try:
            we = WebExtract(
                entity_type=entity_type,
                entity_id=entity_id,
                url=target_url,
                status="failed",
                retrieved_at=now,
                meta={"error": str(e)},
            )
            db.add(we)
            db.add(
                EntityEvent(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    event_type="enrich_failed",
                    payload={"url": target_url, "error": str(e)},
                )
            )
            try:
                db.commit()
            except Exception:
                # If commit fails due to UNIQUE constraint, rollback and return
                # the existing web extract (if any) to avoid raising 409 to callers.
                db.rollback()
                stmt_retry = select(WebExtract).where(
                    WebExtract.entity_type == entity_type,
                    WebExtract.entity_id == entity_id,
                    WebExtract.url == target_url,
                )
                we = db.scalar(stmt_retry)
        except Exception:
            # If even recording the failed extract fails, swallow to preserve
            # original error path and return failure payload below.
            pass

        return {
            "status": "failed",
            "error": str(e),
            "entity_type": entity_type,
            "entity_id": entity_id,
            "url": target_url,
        }
