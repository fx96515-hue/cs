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
    category: "Anbauregionen Peru",
    title: "Top Kaffeeproduzenten",
    description: "Peru ist der 2. größte Bio-Kaffee-Produzent weltweit",
    data: {
      "Produktion 2025": "4.2 Mio. Säcke (60kg)",
      "Weltmarktanteil": "8-10%",
      "Bio-Anteil": "~35%",
      "Fair-Trade-Anteil": "~28%",
      "Hauptregionen": "Cajamarca, San Martin, Amazonas, Junín, Cusco",
      "Anbaufläche": "~430.000 ha",
      "Durchschnittliche Höhe": "1.200 - 2.200 m",
    },
  },
  {
    category: "Sortenvielfalt",
    title: "Kaffee-Varianten",
    description: "Verschiedene Arabica- und Robusta-Sorten",
    data: {
      "Typica": "Klassische peruanische Sorte, niedriger Ertrag, ausgezeichnete Qualität",
      "Bourbon": "Komplexer Geschmack, 600-800m Höhe",
      "Catimor": "Krankheitsresistent, höhere Erträge",
      "Mulatero": "Neue Sorte, trockenheitsresistent",
      "Robusta": "Für günstige Blends, höherer Koffeingehalt",
    },
  },
  {
    category: "Geschmacksprofile",
    title: "Aromen nach Region",
    description: "Typische Geschmacksmerkmale nach Herkunftsregion",
    data: {
      "Cajamarca": "Schokolade, Nuss, ausgewogene Säure, 1.500-1.900m",
      "San Martin": "Fruchtbetont, Zitrus, Johannisbeere, 900-1.800m",
      "Amazonas": "Wildnis-Charakter, grüne Noten, erdig, 600-1.500m",
      "Junín": "Körperreich, süßlich, Malz, 1.600-2.200m",
      "Cusco": "Hell, floral, komplex, höchste Region",
    },
  },
  {
    category: "Ernte & Verarbeitung",
    title: "Verarbeitungsmethoden",
    description: "Von der Kirschtabelle bis zur Verpackung",
    data: {
      "Washed": "74% - Mit Wasser fermentiert, heller, säurebetont",
      "Natural": "20% - Getrocknet mit Frucht, süßer, fruchtiger",
      "Honey": "6% - Zwischen Washed und Natural, süßlich",
      "Erntezeit": "Mai - November (Haupternte)",
      "Trocknungsart": "Überwiegend Patio-Trocknung in der Sonne",
      "Durchschnittlicher Feuchtegehalt": "11-12%",
    },
  },
  {
    category: "Zertifizierungen",
    title: "Qualitäts- & Nachhaltigkeitssiegel",
    description: "Welche Zertifizierungen es gibt",
    data: {
      "Fair Trade": "Mindestpreis $1.40/lb, +$0.20 Premium",
      "Bio (Organic)": "Kein synthetische Pestizide, Bodenaufbau",
      "Rainforest Alliance": "Umwelt- & Sozialstandards",
      "UTZ": "Nachhaltige Farmpraxis, Rückverfolgung",
      "Direct Trade": "Direkt mit Farmer, typisch $3-5/lb",
      "Cup of Excellence": "Hochwertigste Microlots, Auktion",
    },
  },
  {
    category: "Preisentwicklung",
    title: "Marktdaten (Tendenz 2026)",
    description: "Preistrends und Marktfaktoren",
    data: {
      "ICE Arabica (C-Futures)": "~$245/lb (März 2026, hoch)",
      "Rohkaffee Peru (Spot)": "~$165-180/lb FOB",
      "Fair Trade Premium": "+$0.20-0.30 pro Pound",
      "Bio-Premium": "+$0.30-0.50 pro Pound",
      "Haupttreiber": "Brasilien-Dürre, Peru-Produktion hoch",
      "Saisonaler Trend": "Preise fallen typisch Juni-August",
    },
  },
  {
    category: "Versand & Logistik",
    title: "Exportinfrastruktur",
    description: "Von Peru zu deutschen Importeuren",
    data: {
      "Haupthafen": "Callao (Lima) - 97% aller Exporte",
      "Container-Durchschnitt": "20ft = 270 Säcke (60kg)",
      "Frachtkosten": "€45-55 pro Sack Hamburg (2026)",
      "Durchlaufzeit": "4-6 Wochen Callao-Hamburg",
      "Häufigste Route": "Callao → Panama Canal → Hamburg",
      "Versicherung": "Typisch 1-1.5% der Warenwert",
    },
  },
  {
    category: "Deutsche Importe",
    title: "Top Roestereien & Importeure",
    description: "Wer kauft peruanischen Kaffee in Deutschland",
    data: {
      "Hauptzentren": "Hamburg, Bremen, Köln, Berlin",
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
    description: "Wie Kaffeequalität bewertet wird (SCA-Standards)",
    data: {
      "Specialty Grade": "80-100 Punkte - Hochwertig, exportierbar",
      "Premium Grade": "75-79 Punkte - Gut, handelsüblich",
      "Exchange Grade": "70-74 Punkte - Standard-Qualität",
      "Sub-Standard": "<70 Punkte - Industriequalität",
      "Durchschnitt Peru": "82-85 Punkte (Specialty-fokussiert)",
      "Bewertungskriterien": "Aroma, Säure, Körper, Balance, Geschmack, Nachklang",
    },
  },
  {
    category: "Klima & Nachhaltigkeit",
    title: "Anbaubedingungen",
    description: "Geografische & klimatische Faktoren",
    data: {
      "Ideale Temperatur": "15-24°C",
      "Jährlicher Niederschlag": "1.500-3.000mm (Cajamarca-Region)",
      "Bodentyp": "Vulkanische Böden, reich an Mineralien",
      "Höhe (Altitude)": "900m-2.200m (je höher = qualitätvoller)",
      "Schattenpflanzen": "Typisch Waldkakao, Bananen, Flüsse",
      "Biodiversität": "Viele Kaffeefarmen sind Waldschutzgebiete",
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
      "Größte Kooperativen": "100-500 Farmer pro Kooperative",
      "Frauenanteil": "~25% der Farmer (wachsend)",
      "Technologieadoption": "Begrenzt, viele traditionelle Methoden",
    },
  },
  {
    category: "Lagerung & Haltbarkeit",
    title: "Rohkaffee-Standards",
    description: "Wie Rohkaffee lagern sollte",
    data: {
      "Idealtemperatur": "15-20°C",
      "Luftfeuchtigkeit": "60-65%",
      "Lagerdauer": "Max. 6-12 Monate ohne Qualitätseinbußen",
      "Verpackung": "Jutesäcke oder GrainPro (durchlüftet)",
      "Feuchtegehalt": "11-12% (optimal)",
      "Lagerort": "Kühl, dunkel, trocken, gut belüftet",
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
      "Phytosanitäres Zertifikat": "Pflanzenschutzkontrolle",
      "Bill of Lading": "Schiffspapiere vom Hafen",
      "Invoice & Packing List": "Kommerzialdokumente",
    },
  },
  {
    category: "Geschäftsmodelle",
    title: "Wie Kaffeehandel funktioniert",
    description: "Verschiedene Vertriebswege",
    data: {
      "Spot Market": "Kurzfristig, anonyme Käufer, Börsenpreis",
      "Forward Contracts": "Preis heute, Lieferung später",
      "Direct Trade": "Direkt mit Farmer, höherer Preis",
      "Coop Aggregation": "Über Kooperativen (typisch)",
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
            <div style={{ fontSize: "var(--font-size-2xl)", fontWeight: 600 }}>14</div>
            <div className="muted">Info-Kategorien</div>
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: "var(--font-size-2xl)", fontWeight: 600 }}>50+</div>
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
