from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.cooperative import Cooperative
from app.models.market import MarketObservation
from app.models.roaster import Roaster


MARKET_KEYS = [
    "FX:USD_EUR",
    "COFFEE_C:USD_LB",
    "FREIGHT:USD_PER_40FT",
]


def _latest_by_key(
    db: Session, keys: List[str]
) -> Dict[str, Optional[MarketObservation]]:
    out: Dict[str, Optional[MarketObservation]] = {}
    for key in keys:
        out[key] = (
            db.query(MarketObservation)
            .filter(MarketObservation.key == key)
            .order_by(MarketObservation.observed_at.desc())
            .first()
        )
    return out


def _fmt_obs(observation: Optional[MarketObservation]) -> str:
    if not observation:
        return "-"
    value = f"{observation.value:g}"
    unit = f" {observation.unit}" if observation.unit else ""
    currency = f" {observation.currency}" if observation.currency else ""
    timestamp = observation.observed_at.astimezone(timezone.utc).isoformat()
    return f"{value}{unit}{currency} (t={timestamp})"


def _get_top_coops(db: Session) -> List[Cooperative]:
    return (
        db.query(Cooperative)
        .filter(Cooperative.status != "archived")
        .order_by(
            Cooperative.total_score.desc().nullslast(),
            Cooperative.confidence.desc().nullslast(),
            Cooperative.name.asc(),
        )
        .limit(10)
        .all()
    )


def _get_roasters_snapshot(db: Session) -> List[Roaster]:
    return (
        db.query(Roaster)
        .filter(Roaster.status != "archived")
        .order_by(
            Roaster.peru_focus.desc(),
            Roaster.specialty_focus.desc(),
            Roaster.name.asc(),
        )
        .limit(10)
        .all()
    )


def _append_market_section(
    lines: List[str], latest: Dict[str, Optional[MarketObservation]]
) -> None:
    lines.append("## Markt & Preise")
    lines.append(f"- USD->EUR: {_fmt_obs(latest.get('FX:USD_EUR'))}")
    lines.append(f"- Coffee C (USD/lb): {_fmt_obs(latest.get('COFFEE_C:USD_LB'))}")
    lines.append(f"- Fracht 40ft (USD): {_fmt_obs(latest.get('FREIGHT:USD_PER_40FT'))}")
    lines.append("")


def _append_coops_section(lines: List[str], coops: List[Cooperative]) -> None:
    lines.append("## Kooperativen Peru - Top 10")
    if not coops:
        lines.append("- (keine Eintraege)")
        lines.append("")
        return

    for coop in coops:
        score = f"{coop.total_score:.1f}" if coop.total_score is not None else "-"
        confidence = f"{coop.confidence:.2f}" if coop.confidence is not None else "-"
        lines.append(
            f"- **{coop.name}** ({coop.region or 'Region n/a'}) - Score: {score}, Confidence: {confidence}"
        )
        if coop.next_action:
            lines.append(f"  - Next Action: {coop.next_action}")
        if coop.requested_data:
            requested_data = coop.requested_data
            if len(requested_data) > 140:
                requested_data = requested_data[:140] + "..."
            lines.append(f"  - Offene Daten: {requested_data}")
    lines.append("")


def _append_roasters_section(lines: List[str], roasters: List[Roaster]) -> None:
    lines.append("## Roester Deutschland - Auszug")
    if not roasters:
        lines.append("- (keine Eintraege)")
        lines.append("")
        return

    for roaster in roasters:
        flags = []
        if roaster.peru_focus:
            flags.append("Peru")
        if roaster.specialty_focus:
            flags.append("Specialty")
        suffix = f" [{', '.join(flags)}]" if flags else ""
        lines.append(f"- **{roaster.name}** ({roaster.city or 'n/a'}){suffix}")
    lines.append("")


def _append_actions_section(lines: List[str]) -> None:
    lines.append("## Empfohlene Aktionen")
    lines.append(
        "- 1) Fehlende Marktdaten ergaenzen (FX/C-Preis/Fracht) -> verbessert Margenberechnungen"
    )
    lines.append(
        "- 2) Top-3 Kooperativen: Kontaktdaten verifizieren + Muster/Lots anfragen"
    )
    lines.append(
        "- 3) 3-5 passende Roester identifizieren und Gespraech anbahnen (Peru-/Direct-Trade-Fokus)"
    )


def _build_market_payload(
    latest: Dict[str, Optional[MarketObservation]], keys: List[str]
) -> Dict[str, Optional[Dict[str, Any]]]:
    market_payload: Dict[str, Optional[Dict[str, Any]]] = {}
    for key in keys:
        observation = latest.get(key)
        if observation is None:
            market_payload[key] = None
            continue
        market_payload[key] = {
            "value": observation.value,
            "observed_at": observation.observed_at.isoformat(),
        }
    return market_payload


def _build_payload(
    now: datetime,
    latest: Dict[str, Optional[MarketObservation]],
    coops: List[Cooperative],
    roasters: List[Roaster],
) -> Dict[str, Any]:
    return {
        "generated_at": now.isoformat(),
        "market": _build_market_payload(latest, MARKET_KEYS),
        "top_coops": [
            {
                "id": coop.id,
                "name": coop.name,
                "region": coop.region,
                "score": coop.total_score,
                "confidence": coop.confidence,
            }
            for coop in coops
        ],
        "roasters": [
            {
                "id": roaster.id,
                "name": roaster.name,
                "city": roaster.city,
                "peru_focus": roaster.peru_focus,
                "specialty_focus": roaster.specialty_focus,
            }
            for roaster in roasters
        ],
    }


def generate_daily_report(db: Session) -> tuple[str, Dict[str, Any]]:
    """Generate a compact daily report (markdown + structured payload)."""
    now = datetime.now(timezone.utc)
    latest = _latest_by_key(db, MARKET_KEYS)
    coops = _get_top_coops(db)
    roasters = _get_roasters_snapshot(db)

    markdown_lines: List[str] = [
        f"# CoffeeStudio Tagesreport (UTC) - {now.date().isoformat()}",
        "",
    ]

    _append_market_section(markdown_lines, latest)
    _append_coops_section(markdown_lines, coops)
    _append_roasters_section(markdown_lines, roasters)
    _append_actions_section(markdown_lines)

    payload = _build_payload(now, latest, coops, roasters)
    return "\n".join(markdown_lines), payload
