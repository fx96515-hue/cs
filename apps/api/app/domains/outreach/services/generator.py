from __future__ import annotations

from typing import Any, Literal

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.cooperative import Cooperative
from app.models.roaster import Roaster
from app.models.entity_event import EntityEvent
from app.providers.perplexity import PerplexityClient


Language = Literal["de", "en", "es"]
Purpose = Literal["sourcing_pitch", "sample_request"]


def _sourcing_pitch_template(
    language: Language, *, name: str, website: str | None, counterpart: str | None
) -> str:
    if language == "de":
        return (
            f"Hallo {counterpart or 'Team'},\n\n"
            "ich baue gerade ein Direct-Trade-Sourcing fuer Spezialitaetenkaffee aus Peru auf. "
            f"Ich bin auf {name} gestossen{f' ({website})' if website else ''}. "
            "Ich wuerde gerne kurz verstehen, ob ihr grundsaetzlich offen fuer gruene Rohkaffee-Angebote aus Peru seid "
            "(Microlots/Koop-Lots) und wie euer Prozess fuer Samples/Preise aussieht.\n\n"
            "Wenn das passt, schicke ich gerne ein kurzes Profil + erste Lot-Optionen (Region/Varietaet/Processing) "
            "und wir stimmen MOQ/Incoterms ab.\n\n"
            "Viele Gruesse\nCoffeeStudio"
        )
    if language == "en":
        return (
            f"Hi {counterpart or 'team'},\n\n"
            "I'm building a direct-trade sourcing pipeline for specialty coffee from Peru. "
            f"I came across {name}{f' ({website})' if website else ''}. "
            "Are you open to green coffee offers from Peru, and what is your process for samples and pricing?\n\n"
            "If relevant, I can share a short profile and a few lot options (region/variety/processing) and align MOQ/Incoterms.\n\n"
            "Best regards\nCoffeeStudio"
        )
    return (
        f"Hola {counterpart or 'equipo'},\n\n"
        "Estoy construyendo un flujo de abastecimiento direct-trade de cafe de especialidad desde Peru. "
        f"He encontrado {name}{f' ({website})' if website else ''}. "
        "?Estan abiertos a ofertas de cafe verde de Peru y cual es su proceso para muestras y precios?\n\n"
        "Si encaja, puedo enviar un perfil breve y algunas opciones de lotes (region/variedad/proceso) y acordar MOQ/Incoterms.\n\n"
        "Saludos\nCoffeeStudio"
    )


def _sample_request_template(
    language: Language,
    *,
    region: str | None,
    website: str | None,
    contact_hint: str | None,
    counterpart: str | None,
) -> str:
    if language == "de":
        return (
            f"Hallo {counterpart or 'Team'},\n\n"
            f"ich interessiere mich fuer eure Kaffees/Projekte in {region or 'Peru'}. "
            "Koenntet ihr mir bitte sagen, ob Samples (Rohkaffee) moeglich sind und welche Bedingungen gelten "
            "(MOQ, Incoterms, Erntefenster, Preisindikationen)?\n\n"
            f"Kontext: CoffeeStudio - lokales Sourcing/Intelligence-Tool. Website/Quelle: {website or '-'}\n"
            f"Kontakt-Hinweis: {contact_hint or '-'}\n\n"
            "Danke & viele Gruesse\nCoffeeStudio"
        )
    if language == "en":
        return (
            f"Hi {counterpart or 'team'},\n\n"
            "Could you please share if green coffee samples are available and under which terms "
            "(MOQ, Incoterms, harvest window, indicative pricing)?\n\n"
            f"Context: CoffeeStudio sourcing/intelligence. Source: {website or '-'}\n\n"
            "Thanks and best regards\nCoffeeStudio"
        )
    return (
        f"Hola {counterpart or 'equipo'},\n\n"
        "?Seria posible recibir muestras de cafe verde y conocer las condiciones "
        "(MOQ, Incoterms, ventana de cosecha, precios indicativos)?\n\n"
        f"Contexto: CoffeeStudio. Fuente: {website or '-'}\n\n"
        "Gracias y saludos\nCoffeeStudio"
    )


def _template(
    language: Language, *, purpose: Purpose, entity: Any, counterpart: str | None
) -> str:
    name = getattr(entity, "name", "")
    website = getattr(entity, "website", None)
    region = getattr(entity, "region", None)
    contact_hint = getattr(entity, "contact_email", None)

    if purpose == "sourcing_pitch":
        return _sourcing_pitch_template(
            language, name=name, website=website, counterpart=counterpart
        )

    return _sample_request_template(
        language,
        region=region,
        website=website,
        contact_hint=contact_hint,
        counterpart=counterpart,
    )


def generate_outreach(
    db: Session,
    *,
    entity_type: str,
    entity_id: int,
    language: Language = "de",
    purpose: Purpose = "sourcing_pitch",
    counterpart_name: str | None = None,
    refine_with_llm: bool = False,
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

    draft = _template(
        language, purpose=purpose, entity=entity, counterpart=counterpart_name
    )
    used_llm = False

    if refine_with_llm and settings.PERPLEXITY_API_KEY:
        client = PerplexityClient()
        try:
            system = (
                "Du bist ein professioneller Sales/Partnership Writer. "
                "Optimiere den folgenden Text fuer Klarheit, Hoeflichkeit und Kuerze. "
                "Bewahre Fakten, erfinde nichts. Gib NUR den fertigen Text zurueck."
            )
            draft = client.chat_completions(
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": draft},
                ],
                temperature=0.2,
                max_tokens=600,
            ).strip()
            used_llm = True
        finally:
            client.close()

    db.add(
        EntityEvent(
            entity_type=entity_type,
            entity_id=entity_id,
            event_type="outreach_generated",
            payload={"language": language, "purpose": purpose, "used_llm": used_llm},
        )
    )
    db.commit()

    return {
        "status": "ok",
        "entity_type": entity_type,
        "entity_id": entity_id,
        "language": language,
        "purpose": purpose,
        "used_llm": used_llm,
        "text": draft,
    }
