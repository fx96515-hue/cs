from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.cooperative import Cooperative
from app.models.roaster import Roaster
from app.models.market import MarketObservation


def _latest_by_key(
    db: Session, keys: List[str]
) -> Dict[str, Optional[MarketObservation]]:
    out: Dict[str, Optional[MarketObservation]] = {}
    for k in keys:
        out[k] = (
            db.query(MarketObservation)
            .filter(MarketObservation.key == k)
            .order_by(MarketObservation.observed_at.desc())
            .first()
        )
    return out


def _fmt_obs(o: Optional[MarketObservation]) -> str:
    if not o:
        return "-"
    val = f"{o.value:g}"
    unit = f" {o.unit}" if o.unit else ""
    cur = f" {o.currency}" if o.currency else ""
    ts = o.observed_at.astimezone(timezone.utc).isoformat()
    return f"{val}{unit}{cur} (t={ts})"


def generate_daily_report(db: Session) -> tuple[str, Dict]:
    """Generate a compact daily report (markdown + structured payload).

    This intentionally keeps assumptions conservative and highlights missing data.
    """
    now = datetime.now(timezone.utc)

    # Market keys we care about early on
    market_keys = [
        "FX:USD_EUR",
        "COFFEE_C:USD_LB",
        "FREIGHT:USD_PER_40FT",
    ]
    latest = _latest_by_key(db, market_keys)

    # Top coops
    coops = (
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

    # Roasters snapshot
    roasters = (
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

    md_lines: List[str] = []
    md_lines.append(f"# CoffeeStudio Tagesreport (UTC) â€” {now.date().isoformat()}")
    md_lines.append("")

    # Market
    md_lines.append("## Markt & Preise")
    md_lines.append(f"- USDâ†’EUR: {_fmt_obs(latest.get('FX:USD_EUR'))}")
    md_lines.append(f"- Coffee C (USD/lb): {_fmt_obs(latest.get('COFFEE_C:USD_LB'))}")
    md_lines.append(
        f"- Fracht 40ft (USD): {_fmt_obs(latest.get('FREIGHT:USD_PER_40FT'))}"
    )
    md_lines.append("")

    # Coops
    md_lines.append("## Kooperativen Peru â€” Top 10")
    if not coops:
        md_lines.append("- (keine EintrÃ¤ge)")
    else:
        for c in coops:
            score = f"{c.total_score:.1f}" if c.total_score is not None else "-"
            conf = f"{c.confidence:.2f}" if c.confidence is not None else "-"
            md_lines.append(
                f"- **{c.name}** ({c.region or 'Region n/a'}) â€” Score: {score}, Confidence: {conf}"
            )
            if c.next_action:
                md_lines.append(f"  - Next Action: {c.next_action}")
            if c.requested_data:
                md_lines.append(
                    "  - Offene Daten: "
                    + (
                        c.requested_data[:140] + "â€¦"
                        if len(c.requested_data) > 140
                        else c.requested_data
                    )
                )
    md_lines.append("")

    # Roasters
    md_lines.append("## RÃ¶ster Deutschland â€” Auszug")
    if not roasters:
        md_lines.append("- (keine EintrÃ¤ge)")
    else:
        for r in roasters:
            flags = []
            if r.peru_focus:
                flags.append("Peru")
            if r.specialty_focus:
                flags.append("Specialty")
            f = f" [{', '.join(flags)}]" if flags else ""
            md_lines.append(f"- **{r.name}** ({r.city or 'n/a'}){f}")

    md_lines.append("")

    # Actions (very conservative default)
    md_lines.append("## Empfohlene Aktionen")
    md_lines.append(
        "- 1) Fehlende Marktdaten ergÃ¤nzen (FX/C-Preis/Fracht) â†’ verbessert Margenberechnungen"
    )
    md_lines.append(
        "- 2) Top-3 Kooperativen: Kontaktdaten verifizieren + Muster/Lots anfragen"
    )
    md_lines.append(
        "- 3) 3â€“5 passende RÃ¶ster identifizieren und GesprÃ¤ch anbahnen (Peru-/Direct-Trade-Fokus)"
    )

    # Build market dict with proper null checks
    market_dict: Dict[str, Optional[Dict[str, Any]]] = {}
    for k in market_keys:
        obs = latest.get(k)
        if obs is not None:
            market_dict[k] = {
                "value": obs.value,
                "observed_at": obs.observed_at.isoformat(),
            }
        else:
            market_dict[k] = None

    payload: Dict = {
        "generated_at": now.isoformat(),
        "market": market_dict,
        "top_coops": [
            {
                "id": c.id,
                "name": c.name,
                "region": c.region,
                "score": c.total_score,
                "confidence": c.confidence,
            }
            for c in coops
        ],
        "roasters": [
            {
                "id": r.id,
                "name": r.name,
                "city": r.city,
                "peru_focus": r.peru_focus,
                "specialty_focus": r.specialty_focus,
            }
            for r in roasters
        ],
    }

    return "\n".join(md_lines), payload
