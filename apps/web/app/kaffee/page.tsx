'use client'

import Link from 'next/link'
import { useState } from 'react'

interface CoffeeInfo {
  category: string
  title: string
  description: string
  data: Record<string, string>
}

const COFFEE_DATA: CoffeeInfo[] = [
  {
    category: "Geschichte & Kultur",
    title: "Die Geschichte des Kaffees",
    description: "Vom Ursprung in Aethiopien bis zur weltweiten Kultur",
    data: {
      "Kaffee-Legende": "1500er - Ein Hirte in Aethiopien entdeckte belebende Kaffeebohnen",
      "Erstes Kaffeehaus": "1550er - Istanbul, Mekka, Kairo folgen",
      "Europa entdeckt Kaffee": "1600er - Venedig, Holland, Frankreich",
      "Koloniale Expansion": "1700er - Java, Sumatra, Karibik, Brasilien",
      "Industrialisierung": "1800er - Espresso-Maschinen, Loeslicher Kaffee",
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
      "Coffea arabica": "60-70% globale Produktion, 40-50% Koffein, schmackhaft ueberlegene",
      "Coffea robusta": "30-40% globale Produktion, 50-60% Koffein, krankheitsresistent",
      "Blueten": "Kleine weisse Blueten, betnachend suessliches Aroma (Jasmin-aehnlich)",
      "Fruechte": "Kirsche rot (reif) oder gelb, 2 Bohnen pro Frucht (Flat-Bean)",
      "Wachstumszyklus": "3-4 Jahre bis erste Ernte, 25-30 Jahre Lebensdauer",
      "Hoehe": "4-6 Meter wild, 0,5-1,5m kultiviert (fuer Ernte)",
    },
  },
  {
    category: "Chemie & Koffein",
    title: "Was ist in der Kaffeebohne?",
    description: "Chemische Zusammensetzung und Wirkstoffe",
    data: {
      "Koffein": "1-4% - Alkaloid, Stimulant, Abbau in 5-6 Stunden",
      "Chlorogensaeure": "5-10% - Antioxidant, traegt zu Saerue bei",
      "Lipide": "12-15% - Fette, verantwortlich fuer Mouthfeel",
      "Kohlehydrate": "35-40% - Werden bei Roestung karamelisiert",
      "Proteine": "10-12% - Aminosaeuren, Geschmacksbildung",
      "Mineralien": "K, Mg, Ca, P - wichtig fuer Geschmacksprofil",
      "Fluechtiges Aroma": "1000+ verschiedene identifiziert",
      "Saeuern": "3-5% - Chlorogen, Zitronensaeure, Apfelsaeure, Essig",
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
      "Cajamarca": "Schokolade, Nuss, ausgewogene Saerue, 1.500-1.900m",
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
      "Washed": "74% - Mit Wasser fermentiert, heller, saeruebetont",
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
      "Premium Grade": "75-79 Punkte - Gut, handelsueblisch",
      "Exchange Grade": "70-74 Punkte - Standard-Qualitaet",
      "Sub-Standard": "<70 Punkte - Industriequalitaet",
      "Durchschnitt Peru": "82-85 Punkte (Specialty-fokussiert)",
      "Bewertungskriterien": "Aroma, Saerue, Koerper, Balance, Geschmack, Nachklang",
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
      "Lagerdauer": "Max. 6-12 Monate ohne Qualitaetseinbussssen",
      "Verpackung": "Jutesaecke oder GrainPro (durchlueftet)",
      "Feuchtegehalt": "11-12% (optimal)",
      "Lagerort": "Kuehl, dunkel, trocken, gut belueftet",
    },
  },
]

export default function CoffeeInfoPage() {
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set()
  )
  const [searchQuery, setSearchQuery] = useState('')

  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories)
    if (newExpanded.has(category)) {
      newExpanded.delete(category)
    } else {
      newExpanded.add(category)
    }
    setExpandedCategories(newExpanded)
  }

  const filteredData = COFFEE_DATA.filter(
    (item) =>
      item.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      Object.keys(item.data).some((key) =>
        key.toLowerCase().includes(searchQuery.toLowerCase())
      ) ||
      Object.values(item.data).some((value) =>
        value.toLowerCase().includes(searchQuery.toLowerCase())
      )
  )

  return (
    <div style={{ padding: 'var(--space-4)' }}>
      <header style={{ marginBottom: 'var(--space-6)' }}>
        <h1 style={{ marginBottom: 'var(--space-2)' }}>Kaffee-Lexikon</h1>
        <p className="muted">
          Umfassende Informationen zu Kaffee: Anbau, Geschichte, Wissenschaft,
          Handel und mehr
        </p>

        {/* Search Bar */}
        <input
          type="text"
          placeholder="Durchsuchen..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            marginTop: 'var(--space-4)',
            width: '100%',
            maxWidth: '500px',
            padding: 'var(--space-3) var(--space-4)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-lg)',
            fontSize: 'var(--font-size-sm)',
          }}
        />
      </header>

      {/* Stats Bar */}
      <section
        className="panel"
        style={{
          marginBottom: 'var(--space-6)',
          background:
            'linear-gradient(135deg, var(--color-info-subtle) 0%, var(--color-success-subtle) 100%)',
        }}
      >
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: 'var(--space-4)',
          }}
        >
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 600 }}>
              {COFFEE_DATA.length}
            </div>
            <div className="muted">Info-Kategorien</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 600 }}>
              150+
            </div>
            <div className="muted">Datenpunkte</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 600 }}>
              100%
            </div>
            <div className="muted">Oeffentlich zuganglich</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 600 }}>
              2026
            </div>
            <div className="muted">Aktualisiert</div>
          </div>
        </div>
      </section>

      {/* Coffee Info Sections */}
      <section>
        {filteredData.length > 0 ? (
          filteredData.map((item, index) => (
            <div
              key={index}
              className="panel"
              style={{ marginBottom: 'var(--space-4)' }}
            >
              <button
                onClick={() => toggleCategory(item.category)}
                style={{
                  width: '100%',
                  textAlign: 'left',
                  padding: 'var(--space-4)',
                  border: 'none',
                  background: 'none',
                  cursor: 'pointer',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <div
                    style={{
                      display: 'inline-block',
                      background: 'var(--color-info)',
                      color: 'white',
                      padding: '4px 8px',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: 'var(--font-size-xs)',
                      marginBottom: 'var(--space-2)',
                    }}
                  >
                    {item.category}
                  </div>
                  <h3 style={{ margin: 'var(--space-2) 0' }}>{item.title}</h3>
                  <p className="muted" style={{ fontSize: 'var(--font-size-sm)' }}>
                    {item.description}
                  </p>
                </div>
                <div
                  style={{
                    transform: expandedCategories.has(item.category)
                      ? 'rotate(180deg)'
                      : 'rotate(0)',
                    transition: 'transform 0.2s ease',
                  }}
                >
                  ▼
                </div>
              </button>

              {expandedCategories.has(item.category) && (
                <div style={{ padding: '0 var(--space-4) var(--space-4)' }}>
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns:
                        'repeat(auto-fit, minmax(300px, 1fr))',
                      gap: 'var(--space-3)',
                    }}
                  >
                    {Object.entries(item.data).map(([key, value]) => (
                      <div
                        key={key}
                        style={{
                          padding: 'var(--space-3)',
                          background: 'var(--color-bg-muted)',
                          borderRadius: 'var(--radius-md)',
                          border: '1px solid var(--color-border)',
                        }}
                      >
                        <div
                          style={{
                            fontSize: 'var(--font-size-xs)',
                            fontWeight: 600,
                            color: 'var(--color-info)',
                            marginBottom: 'var(--space-1)',
                          }}
                        >
                          {key}
                        </div>
                        <div
                          style={{
                            fontSize: 'var(--font-size-sm)',
                            lineHeight: '1.4',
                          }}
                        >
                          {value}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))
        ) : (
          <div
            style={{
              textAlign: 'center',
              padding: 'var(--space-8)',
              color: 'var(--color-text-muted)',
            }}
          >
            <p>Keine Ergebnisse fuer "{searchQuery}"</p>
          </div>
        )}
      </section>

      {/* Footer */}
      <footer
        style={{
          marginTop: 'var(--space-8)',
          paddingTop: 'var(--space-4)',
          borderTop: '1px solid var(--color-border)',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <span className="muted" style={{ fontSize: 'var(--font-size-xs)' }}>
              Umfassendes Kaffee-Nachschlagewerk fuer Haendler, Roestereien und Enthusiasten
            </span>
          </div>
          <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
            <Link
              href="/markt"
              className="muted"
              style={{
                fontSize: 'var(--font-size-xs)',
                textDecoration: 'none',
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-1)',
              }}
            >
              Marktdaten
            </Link>
            <Link
              href="/ki"
              className="muted"
              style={{
                fontSize: 'var(--font-size-xs)',
                textDecoration: 'none',
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-1)',
              }}
            >
              KI-Assistent
            </Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
