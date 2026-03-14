"use client";

import { useState } from "react";
import Badge from "../components/Badge";

interface CoffeeInfo {
  category: string;
  title: string;
  description: string;
  data: Record<string, string | number | { value: string; info?: string }[]>;
}

const COFFEE_DATA: CoffeeInfo[] = [
  {
    category: "Geschichte & Kultur",
    title: "Die Geschichte des Kaffees",
    description: "Vom Ursprung in Äthiopien bis zur weltweiten Kultur",
    data: {
      "Kaffee-Legende": "1500er - Ein Hirte in Äthiopien entdeckte belebende Kaffeebohnen",
      "Erstes Kaffeehaus": "1550er - Istanbul, Mekka, Kairo folgen",
      "Europa entdeckt Kaffee": "1600er - Venedig, Holland, Frankreich",
      "Koloniale Expansion": "1700er - Java, Sumatra, Karibik, Brasilien",
      "Industrialisierung": "1800er - Espresso-Maschinen, Löslicher Kaffee",
      "Specialty Coffee Movement": "1970er-2000er - Third Wave, Single Origins, Cupping",
      "Aktuelle Trends": "2020er - Nachhaltigkeit, Transparenz, Direct Trade",
    },
  },
  {
    category: "Botanik & Genetik",
    title: "Die Kaffeepflanze",
    description: "Biologische Struktur und genetische Vielfalt",
    data: {
      "Botanische Familie": "Rubiaceae (wie Chinin, Gardenie)",
      "Gattung": "Coffea - 124 bekannte Arten, nur 2 kommerziell (Arabica, Robusta)",
      "Coffea arabica": "60-70% globale Produktion, 40-50% Koffein, geschmacklich überlegen",
      "Coffea robusta": "30-40% globale Produktion, 50-60% Koffein, krankheitsresistent",
      "Blüten": "Kleine weiße Blüten, betäubend süßliches Aroma (Jasmin-ähnlich)",
      "Früchte": "Kirsche rot (reif) oder gelb, 2 Bohnen pro Frucht (Flat-Bean)",
      "Wachstumszyklus": "3-4 Jahre bis erste Ernte, 25-30 Jahre Lebensdauer",
      "Höhe": "4-6 Meter wild, 0,5-1,5m kultiviert (für Ernte)",
    },
  },
  {
    category: "Chemie & Koffein",
    title: "Was ist in der Kaffeebohne?",
    description: "Chemische Zusammensetzung und Wirkstoffe",
    data: {
      "Koffein": "1-4% - Alkaloid, Stimulant, Abbau in 5-6 Stunden",
      "Chlorogensäure": "5-10% - Antioxidant, trägt zu Säure bei",
      "Lipide": "12-15% - Fette, verantwortlich für Mouthfeel",
      "Kohlehydrate": "35-40% - Werden bei Röstung karamelisiert",
      "Proteine": "10-12% - Aminosäuren, Geschmacksbildung",
      "Mineralien": "K, Mg, Ca, P - wichtig für Geschmacksprofil",
      "Flüchtige Aromastoffe": "1000+ verschiedene identifiziert",
      "Säuren": "3-5% - Chlorogen, Zitronensäure, Apfelsäure, Essig",
    },
  },
  {
    category: "Röstung & Chemie",
    title: "Was passiert bei der Röstung?",
    description: "Maillard-Reaktion und Karamelisierung",
    data: {
      "Rohe Bohne": "Grün, unauffällig, sauer, grässlich",
      "Light Roast (160-180°C)": "Zitrus, helle Säure, fruchtbetont, Specialty-Fokus",
      "Medium Roast (180-200°C)": "Ausgewogene Säure & Körper, Frühstücks-Standard",
      "Dark Roast (200-220°C)": "Kräftig, bitter-süß, Espresso-Standard",
      "Maillard-Reaktion": "Aminosäuren + Zucker → 1000+ neue Geschmacksmoleküle ab 140°C",
      "Caramelisierung": "Zucker brechen ab ca. 160°C auf → braun",
      "Degassing": "CO2-Freisetzung nach Röstung, Peak 24-48 Stunden",
      "Lagerstabilität": "Leicht/Medium 4-6 Wochen, Dark bis zu 8 Wochen",
    },
  },
  {
    category: "Zubereitung & Extraction",
    title: "Wie bereitet man Kaffee zu?",
    description: "Verschiedene Brühmethoden und deren Chemie",
    data: {
      "Espresso": "9 bar Druck, 25-30 sec, 20-40ml Output - konzentriert, dicke Crema",
      "Filterkaffee": "Gravity-Flow, 3-4 min - sauber, hell, transparent",
      "French Press": "Immersion 4 min - voller Körper, Öle bleiben",
      "Moka Pot": "Dampfdruck 1-2 bar, stove-top - kräftig wie Espresso",
      "Turkish": "Fein gemahlenes Pulver, Wasser 1:1, gekocht 3x - samtig",
      "Kaltwasser (Cold Brew)": "12-24h immersion, low acidity - süß, mild",
      "Ideal-Parameter": "Wasser 200°F (93°C), Verhältnis 1:16-18, 25-35 sec contact",
      "Extraction Yield": "18-22% - Geschmack, >22% bitter, <18% sauer",
    },
  },
  {
    category: "Gesundheit & Wissenschaft",
    title: "Kaffeee & Gesundheit",
    description: "Was sagt die Forschung?",
    data: {
      "Koffein-Toleranz": "Nach 3-4 Tagen, Entzugssymptome möglich bei >400mg/Tag",
      "Optimale Dosis": "200-400mg täglich (3-5 Tassen) für erwachsene",
      "Schlafqualität": "Halbwertszeit 5-6h, nachts <200mg nach 15 Uhr ideal",
      "Metabolismus": "CYP1A2-Gen bestimmt Verarbeitung - Schnell vs. Slow Metabolizer",
      "Kardiovaskulär": "Moderate Mengen nicht schädlich, für Hypertonie OK ab <300mg",
      "Kognition": "Alertness +25%, Reaktionszeit -9%, Kreativität +11%",
      "Antioxidanten": "Chlorogensäure, Polyphenole - entzündungshemmend",
      "Nebenwirkungen": "Jitteriness, Anxiety, Sleep Disruption, Acid Reflux bei Überkonsum",
    },
  },
  {
    category: "Schmecken & Sensorik",
    title: "Die Geschmackssinn-Wissenschaft",
    description: "Warum schmecken manche Kaffeesorten anders?",
    data: {
      "Zunge": "Nicht 5 Geschmäcker (süß, salzig, sauer, bitter, umami), sondern bis zu 15!",
      "Aromamoleküle": "1000+ Volatile, hauptsächlich durch Geruchssinn (retronasal)",
      "Körper": "Fette + Suspendierte Partikel = Mundgefühl/Viscosity",
      "Säure": "Chlorogensäure, Zitronensäure, Äpfelsäure - fruchtiges Profil",
      "Bitter": "Bitter-Rezeptoren auf Zunge, Koffein + Röstprodukte",
      "Süße": "Natürliche Zucker + Karamelize während Röstung",
      "Terroir": "Altitude, Boden, Wasser, Klima - wie bei Wein",
      "Tasting Notes": "Basis-Vokabular: Floral, Fruity, Herbal, Spicy, Nutty, Chocolatey",
    },
  },
  {
    category: "Nachhaltigkeit & Anbau",
    title: "Umweltliche & Soziale Themen",
    description: "Die Zukunft des Kaffeebaus",
    data: {
      "Wasserbedarf": "140 Liter Wasser für 1 Tasse Kaffee (Anbau bis Verarbeitung)",
      "Bodenerschöpfung": "Monokultur reduziert Bodenqualität, Erosion in 5-10 Jahren",
      "Waldzerstörung": "~2.5 Mrd Kaffee-Bäume = ~6 Mrd ha Land, oft durch Rodung",
      "Pestizide": "Chemikalien-Einsatz höher als bei anderen Feldfrüchten",
      "Farmer-Einkommen": "Nur 10-15% des Retail-Preises erreicht den Farmer",
      "Klimawandel": "Ideal-Zone schrumpft, Arabica um 50% bis 2050 gefährdet",
      "Schattenkaffee": "Unter Bäumen angebaut = Waldsystem mit +50% Biodiversität",
      "Regenerative": "Kompost, Mulch, Leguminosen statt Monokultur",
    },
  },
  {
    category: "Handelsabläufe",
    title: "Vom Farmer zur Rösterei",
    description: "Die Supply Chain im Detail",
    data: {
      "Farmer": "Erntet Kirschen (Mai-Nov), fermentiert, trocknet",
      "Kooperative": "Aggregiert von 50-500 Farmern, Qualitätskontrolle, erste Röstung",
      "Exporter": "Verpackt in 60kg Säcke, Zertifikate, Arrangement",
      "Hafen": "Callao (Lima) - Customs, Container, Lagerung",
      "Schiff": "4-6 Wochen Panama Canal Route → Hamburg",
      "Hafen D": "Hamburg, Bremen - Entladung, Zoll, Lagerung",
      "Importeur": "Lagert, Rohkaffee-Tests, Verkauf an Röstereien",
      "Rösterei": "Lagert 2-6 Monate, kleine Röstung (Sample), Verkauf",
      "Einzelhandel": "2-4 Wochen Lagerung vor Verkauf an Konsument",
      "Konsument": "Kauft, lagert 2-8 Wochen, Zubereitung",
    },
  },
  {
    category: "Quality Control",
    title: "Wie wird Kaffee überprüft?",
    description: "Standards von Ernte bis Röstung",
    data: {
      "Green Bean Test": "Fehlerhaft? Verformung, Verfärbung, Insektenlöcher, Schimmel",
      "Washed vs. Natural": "Prozessgeschmack, Feuchte 11-12%, visuelle Inspektion",
      "Sample Roast": "Kleine Probe geroestet zur Qualitätsprobe vor Kauf",
      "Cupping": "SCA-Standard: 5 Tassen, blind testen, 16+ Kriterien",
      "Score Sheet": "10 Kategorien × 10 Punkte = max 100 Punkte (80+ Specialty)",
      "Defect Count": "Quaker (unfermentiert), Black (Schimmel), Broken (zerbrochen)",
      "Moisture": ">12% = Schimmelrisiko, <10% = zu trocken/brüchig",
      "Purity": "Fremdkörper? Kleine Steine, Holz, Metall müssen raus",
    },
  },
  {
    category: "Rösterei-Betrieb",
    title: "Wie eine Rösterei funktioniert",
    description: "Von Rohkaffee zur gebrauten Tasse",
    data: {
      "Equipment": "Trommel/Fluid Bed Röster (5-50kg batch), Kühlbett, Verpackung",
      "Rohkaffee": "Eingekauft in 60kg Säcken, 6-12 Monate vorgelagert",
      "Lagering": "15-20°C, 60-65% Feuchtigkeit, Belüftung optimal",
      "Röst-Profil": "Temperatur + Zeit = Farbe, Körper, Aroma-Entwicklung",
      "Cupping-Program": "Neue Chargen kosten, bestehende 1x Woche getestet",
      "Blends": "Mehrere Ursprünge mischen für Konsistenz + Geschmack",
      "Verpackung": "Ventil-Beutel (Degassing), Kinder-sichere Verschlüsse",
      "Versand": "2-3 Tage nach Röstung optimal, 4 Wochen Peak-Genuss",
    },
  },
  {
    category: "Lagertechniken",
    title: "So lagert man Kaffee richtig",
    description: "Maximale Frische über Wochen",
    data: {
      "Nach Röstung": "24-48h Degassing nötig vor Verbrauch (CO2 entweicht)",
      "Luftdicht": "Vakuum oder Inert-Gas (Stickstoff) verhindert Oxidation",
      "Kühl & Trocken": "15-20°C ideal, nicht im Kühlschrank (Kondenswasser!)",
      "Dunkel": "UV-Licht zerstört Aromen, Opaque Container oder dunkle Lagerung",
      "Geruchsstoffe": "Kaffee nimmt Gerüche auf - nicht neben Zwiebel/Fisch",
      "Peak-Fenster": "Light Roast: 2-4 Wochen, Dark Roast: 4-8 Wochen",
      "Gemahlener Kaffee": "10-20x schneller degrading (Oberfläche), 1-2 Wochen max",
      "Einfrieren": "Okay 1-3 Monate, aber Kondenswasser problematisch beim Auftauen",
    },
  },
  {
    category: "Geschäftskunde",
    title: "Kaffee für Cafés & Restaurants",
    description: "Professionelle Bezugsquellen",
    data: {
      "Großimporteur": "100+ Tonnen/Jahr, Direktkontakt zu Exporteuren",
      "Distributor": "Lagert, bietet Varianten, Liefertreue, kleinere Mengen",
      "Specialty Roaster": "5-50 Tonnen/Jahr, Single Origins, Relation zum Farmer",
      "Online B2B": "Direkter Zugang zu Rohkaffee, Pre-Order Möglichkeit",
      "Pricing": "GradeSpot/ICE = €90-120/50kg, Fair Trade +€20-30, Bio +€30-50",
      "MOQ": "Oft 500kg-1000kg Mindestkauf, kleinere via Distributor",
      "Vertrag": "Forward (6-12 Monate), Spot (sofort), Konsignation (zahle später)",
      "Support": "Technische Beratung, Lagertipps, Kostproben, Training",
    },
  },
  {
    category: "Innovationen & Trends",
    title: "Die Zukunft des Kaffees",
    description: "Neue Technologien und Ansätze",
    data: {
      "Lab-grown Coffee": "Biotechnologie - Kaffee-Moleküle ohne Anbau (noch experimentell)",
      "Shade-Grown Certification": "Biodiversität + Walschutz - Premium-Segment",
      "Traceability/Blockchain": "QR-Code auf Packung = genaue Farm-Geschichte",
      "Specialty Micro-Lots": "10-50kg Chargen von einzelnen Parzellen, bis $20/lb",
      "Climate-Adaptive Varieties": "Neue Hybriden gegen Dürre & Krankheiten züchten",
      "Direct Trade 2.0": "Farmer + Rösterei Online-Plattformen, faire Preise",
      "Cold Brew Konz.": "Fertig-Konzentrate für Gastronomie & Retail",
      "AI-Cupping": "Spektroskopie zur automatischen Qualitätsbewertung (Prototyp)",
    },
  },
  {
    category: "Anbauregionen Peru",
    title: "Top Kaffeeproduzenten",
    description: "Peru ist der 2. groesste Bio-Kaffee-Produzent weltweit",
    data: {
      "Produktion 2025": "4.2 Mio. Saecke (60kg)",
      "Weltmarktanteil": "8-10%",
      "Bio-Anteil": "~35%",
      "Fair-Trade-Anteil": "~28%",
      "Hauptregionen": "Cajamarca, San Martin, Amazonas, Junin, Cusco",
      "Anbauflaeche": "~430.000 ha",
      "Durchschnittliche Hoehe": "1.200 - 2.200 m",
    },
  },
  {
    category: "Sortenvielfalt",
    title: "Kaffee-Varianten",
    description: "Verschiedene Arabica- und Robusta-Sorten",
    data: {
      "Typica": "Klassische peruanische Sorte, niedriger Ertrag, ausgezeichnete Qualitaet",
      "Bourbon": "Komplexer Geschmack, 600-800m Hoehe",
      "Catimor": "Krankheitsresistent, hoehere Ertraege",
      "Mulatero": "Neue Sorte, trockenheitsresistent",
      "Robusta": "Fuer guenstige Blends, hoeherer Koffeingehalt",
    },
  },
  {
    category: "Geschmacksprofile",
    title: "Aromen nach Region",
    description: "Typische Geschmacksmerkmale nach Herkunftsregion",
    data: {
      "Cajamarca": "Schokolade, Nuss, ausgewogene Saeure, 1.500-1.900m",
      "San Martin": "Fruchtbetont, Zitrus, Johannisbeere, 900-1.800m",
      "Amazonas": "Wildnis-Charakter, gruene Noten, erdig, 600-1.500m",
      "Junin": "Koerperreich, suesslich, Malz, 1.600-2.200m",
      "Cusco": "Hell, floral, komplex, hoechste Region",
    },
  },
  {
    category: "Ernte & Verarbeitung",
    title: "Verarbeitungsmethoden",
    description: "Von der Kirschtabelle bis zur Verpackung",
    data: {
      "Washed": "74% - Mit Wasser fermentiert, heller, saeurebetont",
      "Natural": "20% - Getrocknet mit Frucht, suesser, fruchtiger",
      "Honey": "6% - Zwischen Washed und Natural, suesslich",
      "Erntezeit": "Mai - November (Haupternte)",
      "Trocknungsart": "Ueberwiegend Patio-Trocknung in der Sonne",
      "Durchschnittlicher Feuchtegehalt": "11-12%",
    },
  },
  {
    category: "Zertifizierungen",
    title: "Qualitaets- & Nachhaltigkeitssiegel",
    description: "Welche Zertifizierungen es gibt",
    data: {
      "Fair Trade": "Mindestpreis $1.40/lb, +$0.20 Premium",
      "Bio (Organic)": "Kein synthetische Pestizide, Bodenaufbau",
      "Rainforest Alliance": "Umwelt- & Sozialstandards",
      "UTZ": "Nachhaltige Farmpraxis, Rueckverfolgung",
      "Direct Trade": "Direkt mit Farmer, typisch $3-5/lb",
      "Cup of Excellence": "Hochwertigste Microlots, Auktion",
    },
  },
  {
    category: "Preisentwicklung",
    title: "Marktdaten (Tendenz 2026)",
    description: "Preistrends und Marktfaktoren",
    data: {
      "ICE Arabica (C-Futures)": "~$245/lb (Maerz 2026, hoch)",
      "Rohkaffee Peru (Spot)": "~$165-180/lb FOB",
      "Fair Trade Premium": "+$0.20-0.30 pro Pound",
      "Bio-Premium": "+$0.30-0.50 pro Pound",
      "Haupttreiber": "Brasilien-Duerre, Peru-Produktion hoch",
      "Saisonaler Trend": "Preise fallen typisch Juni-August",
    },
  },
  {
    category: "Versand & Logistik",
    title: "Exportinfrastruktur",
    description: "Von Peru zu deutschen Importeuren",
    data: {
      "Haupthafen": "Callao (Lima) - 97% aller Exporte",
      "Container-Durchschnitt": "20ft = 270 Saecke (60kg)",
      "Frachtkosten": "EUR 45-55 pro Sack Hamburg (2026)",
      "Durchlaufzeit": "4-6 Wochen Callao-Hamburg",
      "Haeufigste Route": "Callao - Panama Canal - Hamburg",
      "Versicherung": "Typisch 1-1.5% der Warenwert",
    },
  },
  {
    category: "Deutsche Importe",
    title: "Top Roestereien & Importeure",
    description: "Wer kauft peruanischen Kaffee in Deutschland",
    data: {
      "Hauptzentren": "Hamburg, Bremen, Koeln, Berlin",
      "Durchschnittliche Roesterei": "50-500 Tonnen/Jahr",
      "Specialty Roestereien": "5-50 Tonnen/Jahr (Premium-Segmente)",
      "Direktimporte": "150+ Importeure bundesweit",
      "Beliebte Regionen": "Cajamarca (60%), San Martin (25%), Amazonas (15%)",
      "Fokus": "Bio, Fair Trade, Specialty Grade",
    },
  },
  {
    category: "Sensorische Bewertung",
    title: "Cupping-Standards",
    description: "Wie Kaffeequalitaet bewertet wird (SCA-Standards)",
    data: {
      "Specialty Grade": "80-100 Punkte - Hochwertig, exportierbar",
      "Premium Grade": "75-79 Punkte - Gut, handelsueblich",
      "Exchange Grade": "70-74 Punkte - Standard-Qualitaet",
      "Sub-Standard": "<70 Punkte - Industriequalitaet",
      "Durchschnitt Peru": "82-85 Punkte (Specialty-fokussiert)",
      "Bewertungskriterien": "Aroma, Saeure, Koerper, Balance, Geschmack, Nachklang",
    },
  },
  {
    category: "Klima & Nachhaltigkeit",
    title: "Anbaubedingungen",
    description: "Geografische & klimatische Faktoren",
    data: {
      "Ideale Temperatur": "15-24 Grad C",
      "Jaehrlicher Niederschlag": "1.500-3.000mm (Cajamarca-Region)",
      "Bodentyp": "Vulkanische Boeden, reich an Mineralien",
      "Hoehe (Altitude)": "900m-2.200m (je hoeher = qualitaetvoller)",
      "Schattenpflanzen": "Typisch Waldkakao, Bananen, Fluesse",
      "Biodiversitaet": "Viele Kaffeefarmen sind Waldschutzgebiete",
    },
  },
  {
    category: "Kooperativen & Farmer",
    title: "Produzentenstruktur",
    description: "Wer produziert den peruanischen Kaffee",
    data: {
      "Kleinbauern": "~90% (durchschn. 0,5-3 Hektar)",
      "Durchschnittliches Einkommen": "$2.000-4.000/Jahr pro Farm",
      "Kooperativen": "~200 registrierte Kooperativen",
      "Groesste Kooperativen": "100-500 Farmer pro Kooperative",
      "Frauenanteil": "~25% der Farmer (wachsend)",
      "Technologieadoption": "Begrenzt, viele traditionelle Methoden",
    },
  },
  {
    category: "Lagerung & Haltbarkeit",
    title: "Rohkaffee-Standards",
    description: "Wie Rohkaffee lagern sollte",
    data: {
      "Idealtemperatur": "15-20 Grad C",
      "Luftfeuchtigkeit": "60-65%",
      "Lagerdauer": "Max. 6-12 Monate ohne Qualitaetseinbussen",
      "Verpackung": "Jutesaecke oder GrainPro (durchlueftet)",
      "Feuchtegehalt": "11-12% (optimal)",
      "Lagerort": "Kuehl, dunkel, trocken, gut belueftet",
    },
  },
  {
    category: "Export-Dokumentation",
    title: "Papierkrieg beim Export",
    description: "Erforderliche Zertifikate und Unterlagen",
    data: {
      "Herkunftszertifikat": "Beweist peruanischen Ursprung",
      "Bio-Zertifikat": "Falls Bio (Control Union, Ecocert, u.a.)",
      "Fair-Trade-Zertifikat": "Falls Fair Trade (FLO, Fair Trade USA)",
      "Phytosanitaeres Zertifikat": "Pflanzenschutzkontrolle",
      "Bill of Lading": "Schiffspapiere vom Hafen",
      "Invoice & Packing List": "Kommerzialdokumente",
    },
  },
  {
    category: "Geschaeftsmodelle",
    title: "Wie Kaffeehandel funktioniert",
    description: "Verschiedene Vertriebswege",
    data: {
      "Spot Market": "Kurzfristig, anonyme Kaeufer, Boersenpreis",
      "Forward Contracts": "Preis heute, Lieferung spaeter",
      "Direct Trade": "Direkt mit Farmer, hoeherer Preis",
      "Coop Aggregation": "Ueber Kooperativen (typisch)",
      "Exporter": "Peruvian Export Houses als Mittler",
      "Auktionen": "Cup of Excellence, Speciality Auctions",
    },
  },
];

export default function CoffeeInfoPage() {
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  const filteredData = COFFEE_DATA.filter(
    (item) =>
      item.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <>
      {/* Page Header */}
      <header className="pageHeader">
        <div className="pageHeaderContent">
          <h1 className="h1">Kaffee-Lexikon</h1>
          <p className="subtitle">
            Umfassende Informationen zu peruanischem Kaffee - Anbau, Verarbeitung, Handel, Qualität
          </p>
        </div>
      </header>

      {/* Search */}
      <section className="panel" style={{ marginBottom: "var(--space-6)" }}>
        <input
          type="text"
          placeholder="Durchsuche alle Kategorien..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={{
            width: "100%",
            padding: "var(--space-3) var(--space-4)",
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-lg)",
            fontSize: "var(--font-size-base)",
            background: "var(--color-surface)",
          }}
        />
      </section>

      {/* Info Sections */}
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
        {filteredData.map((section) => (
          <section
            key={section.title}
            className="panel"
            style={{
              cursor: "pointer",
              transition: "all 0.2s ease",
            }}
            onClick={() =>
              setExpandedCategory(expandedCategory === section.title ? null : section.title)
            }
          >
            <div className="panelHeader">
              <div>
                <h2 className="panelTitle">{section.title}</h2>
                <p className="subtitle">{section.description}</p>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                <Badge tone="info">{section.category}</Badge>
                <span style={{ fontSize: "var(--font-size-xl)" }}>
                  {expandedCategory === section.title ? "▼" : "▶"}
                </span>
              </div>
            </div>

            {expandedCategory === section.title && (
              <div className="panelBody">
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
                    gap: "var(--space-4)",
                  }}
                >
                  {Object.entries(section.data).map(([key, value]) => (
                    <div
                      key={key}
                      style={{
                        padding: "var(--space-3)",
                        background: "var(--color-bg-muted)",
                        borderRadius: "var(--radius-md)",
                        borderLeft: "3px solid var(--color-primary)",
                      }}
                    >
                      <div
                        style={{
                          fontSize: "var(--font-size-xs)",
                          color: "var(--color-text-muted)",
                          textTransform: "uppercase",
                          letterSpacing: "0.05em",
                          marginBottom: "var(--space-1)",
                        }}
                      >
                        {key}
                      </div>
                      <div style={{ fontSize: "var(--font-size-base)", fontWeight: 500 }}>
                        {typeof value === "object" && !Array.isArray(value)
                          ? String(value)
                          : Array.isArray(value)
                          ? value
                              .map((item) =>
                                typeof item === "string"
                                  ? item
                                  : `${item.value} ${item.info ? `(${item.info})` : ""}`
                              )
                              .join(", ")
                          : value}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>
        ))}
      </div>

      {/* Stats Bar */}
      <section
        className="panel"
        style={{
          marginTop: "var(--space-6)",
          background: "linear-gradient(135deg, var(--color-info-subtle) 0%, var(--color-success-subtle) 100%)",
        }}
      >
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "var(--space-4)" }}>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: "var(--font-size-2xl)", fontWeight: 600 }}>26</div>
            <div className="muted">Info-Kategorien</div>
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: "var(--font-size-2xl)", fontWeight: 600 }}>150+</div>
            <div className="muted">Datenpunkte</div>
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: "var(--font-size-2xl)", fontWeight: 600 }}>100%</div>
            <div className="muted">Öffentlich zugänglich</div>
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: "var(--font-size-2xl)", fontWeight: 600 }}>2026</div>
            <div className="muted">Aktualisiert</div>
          </div>
        </div>
      </section>

      {/* Sources */}
      <section className="panel" style={{ marginTop: "var(--space-6)" }}>
        <div className="panelHeader">
          <h2 className="panelTitle">Quellen & Ressourcen</h2>
        </div>
        <div className="panelBody">
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "var(--space-3)" }}>
            <div>
              <strong>Peruanische Institutionen</strong>
              <ul style={{ marginTop: "var(--space-2)", paddingLeft: "var(--space-4)" }}>
                <li>JNC - Junta Nacional del Café</li>
                <li>INEI - Statistikbüro</li>
                <li>BCRP - Zentralbank (Exportdaten)</li>
              </ul>
            </div>
            <div>
              <strong>Internationale Standards</strong>
              <ul style={{ marginTop: "var(--space-2)", paddingLeft: "var(--space-4)" }}>
                <li>SCA - Specialty Coffee Association</li>
                <li>ICE - Intercontinental Exchange</li>
                <li>Fair Trade International</li>
              </ul>
            </div>
            <div>
              <strong>Deutsche Quellen</strong>
              <ul style={{ marginTop: "var(--space-2)", paddingLeft: "var(--space-4)" }}>
                <li>DKV - Deutscher Kaffee Verband</li>
                <li>BZfE - Bundeszentrale</li>
                <li>Freightos - Container-Raten</li>
              </ul>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
