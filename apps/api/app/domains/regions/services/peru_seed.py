from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.peru_region import PeruRegion


DEFAULT_REGIONS: list[dict[str, Any]] = [
    {
        "code": "CAJ",
        "name": "Cajamarca",
        "description_de": "Nordperu, bekannt für klare, süße Profile; häufig Kooperativen mit Exporterfahrung.",
        "altitude_range": "1200–2000m",
        "typical_varieties": "Bourbon, Caturra, Typica",
        "typical_processing": "Washed (häufig), teils Honey",
        "logistics_notes": "Inland per LKW Richtung Küste/Lima; Saisonabhängigkeit bei Regen.",
        "risk_notes": "Regenzeiten können Straßen beeinträchtigen; Qualität schwankt je nach Trocknung.",
    },
    {
        "code": "JUN",
        "name": "Junín (Satipo/Chanchamayo)",
        "description_de": "Zentralperu; viele Kleinerzeuger, oft Kooperativen.",
        "altitude_range": "1200–1800m",
        "typical_varieties": "Caturra, Catuaí, Typica",
        "typical_processing": "Washed; zunehmend experimentelle Fermentation",
        "logistics_notes": "Achse über La Merced; Inland-Transit nach Callao.",
        "risk_notes": "Transportzeit/Temperaturmanagement; Ernteschwankungen.",
    },
    {
        "code": "SAM",
        "name": "San Martín",
        "description_de": "Nördliche Anden/Amazonas-Ausläufer; teils organisch zertifiziert.",
        "altitude_range": "900–1700m",
        "typical_varieties": "Caturra, Catuaí, Bourbon",
        "typical_processing": "Washed; teils Natural",
        "logistics_notes": "Inland über Tarapoto/Moyobamba; längere Vorläufe.",
        "risk_notes": "Hohe Luftfeuchtigkeit → Trocknungsrisiko; Saisonregen.",
    },
    {
        "code": "CUS",
        "name": "Cusco (La Convención)",
        "description_de": "Südostperu; hohe Höhenlagen, oft sehr komplexe Profile.",
        "altitude_range": "1400–2200m",
        "typical_varieties": "Typica, Bourbon, Caturra",
        "typical_processing": "Washed; teils Honey",
        "logistics_notes": "Inland teils anspruchsvoll (Gebirge); Sammelstellen entscheidend.",
        "risk_notes": "Straßen/Erdrutsche möglich; längere Lieferketten.",
    },
    {
        "code": "PUN",
        "name": "Puno (Sandia)",
        "description_de": "Südperu nahe Bolivien; bekannt für sehr süße, florale Profile.",
        "altitude_range": "1500–2300m",
        "typical_varieties": "Bourbon, Typica, Caturra",
        "typical_processing": "Washed; teils Natural",
        "logistics_notes": "Lange Inlandwege; Planung der Konsolidierung wichtig.",
        "risk_notes": "Hohe Komplexität in der Logistik; Klimaextreme möglich.",
    },
    {
        "code": "AMA",
        "name": "Amazonas",
        "description_de": "Nordperu; bergige Zonen, oft kleine Lots mit klarer Säure.",
        "altitude_range": "1200–2100m",
        "typical_varieties": "Caturra, Bourbon, Typica",
        "typical_processing": "Washed",
        "logistics_notes": "Inland abhängig von Straßenlage; Sammelstellen/Koops wichtig.",
        "risk_notes": "Wetter/Infrastructure; Qualität hängt stark von Aufbereitung ab.",
    },
]


def seed_default_regions(db: Session) -> dict[str, Any]:
    created = 0
    updated = 0
    for r in DEFAULT_REGIONS:
        stmt = select(PeruRegion).where(PeruRegion.code == r["code"])
        obj = db.scalar(stmt)
        if not obj:
            obj = PeruRegion(code=r["code"], name=r["name"])
            db.add(obj)
            created += 1
        else:
            updated += 1
        for k in [
            "description_de",
            "altitude_range",
            "typical_varieties",
            "typical_processing",
            "logistics_notes",
            "risk_notes",
        ]:
            if r.get(k) and not getattr(obj, k):
                setattr(obj, k, r[k])
    db.commit()
    return {
        "status": "ok",
        "created": created,
        "updated": updated,
        "total": len(DEFAULT_REGIONS),
    }
