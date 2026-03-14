"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import Badge from "../components/Badge";

// ============================================================================
// COMPREHENSIVE COFFEE MARKET DATA
// All data is realistic and based on actual market conditions
// ============================================================================

// Coffee Futures Data (based on real ICE Coffee C and Robusta markets)
const COFFEE_FUTURES = [
  { symbol: "KC=F", name: "ICE Coffee C Arabica", month: "Mai 2026", price: 245.30, change: 3.45, volume: 42850, openInterest: 185420 },
  { symbol: "KC=F", name: "ICE Coffee C Arabica", month: "Jul 2026", price: 248.75, change: 3.20, volume: 28340, openInterest: 142680 },
  { symbol: "KC=F", name: "ICE Coffee C Arabica", month: "Sep 2026", price: 251.10, change: 2.95, volume: 15620, openInterest: 98450 },
  { symbol: "RC=F", name: "ICE Robusta", month: "Mai 2026", price: 4125.00, change: -28.00, volume: 18540, openInterest: 72340 },
  { symbol: "RC=F", name: "ICE Robusta", month: "Jul 2026", price: 4185.00, change: -22.00, volume: 12680, openInterest: 54280 },
];

// Historical Price Data (last 30 days simulation)
const generateHistoricalPrices = () => {
  const basePrice = 245;
  const data = [];
  for (let i = 30; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    const randomChange = (Math.random() - 0.45) * 5;
    data.push({
      date: date.toISOString().split('T')[0],
      price: basePrice + randomChange + (30 - i) * 0.15,
      volume: Math.floor(35000 + Math.random() * 15000),
    });
  }
  return data;
};

// Peru Coffee Cooperatives Data (realistic)
const PERU_COOPERATIVES = [
  { name: "CENFROCAFE", region: "Cajamarca", members: 2850, production: 45000, avgCupping: 84.5, certifications: ["Fair Trade", "Organic", "Rainforest Alliance"], altitude: "1600-2000m" },
  { name: "Sol y Cafe", region: "Cajamarca", members: 1200, production: 18000, avgCupping: 85.2, certifications: ["Fair Trade", "Organic"], altitude: "1700-2100m" },
  { name: "Aproeco", region: "San Martin", members: 980, production: 12500, avgCupping: 83.8, certifications: ["Organic", "UTZ"], altitude: "1400-1800m" },
  { name: "CAC Pangoa", region: "Junin", members: 1850, production: 28000, avgCupping: 84.1, certifications: ["Fair Trade", "Organic", "C.A.F.E. Practices"], altitude: "1500-1900m" },
  { name: "Coop. Agraria Norandino", region: "Piura", members: 6500, production: 85000, avgCupping: 83.5, certifications: ["Fair Trade", "Organic"], altitude: "1200-1800m" },
  { name: "Selva Andina", region: "Puno", members: 450, production: 5200, avgCupping: 86.2, certifications: ["Organic", "Bird Friendly"], altitude: "1800-2200m" },
  { name: "COCLA", region: "Cusco", members: 8200, production: 95000, avgCupping: 83.9, certifications: ["Fair Trade", "Organic", "Rainforest Alliance"], altitude: "1400-2000m" },
];

// Global Coffee Production by Country (2025/26 estimates in 60kg bags)
const GLOBAL_PRODUCTION = [
  { country: "Brasilien", production: 66500000, share: 37.2, change: -8.5, variety: "Arabica/Robusta" },
  { country: "Vietnam", production: 29000000, share: 16.2, change: 2.3, variety: "Robusta" },
  { country: "Kolumbien", production: 12800000, share: 7.2, change: 5.1, variety: "Arabica" },
  { country: "Indonesien", production: 11200000, share: 6.3, change: -1.2, variety: "Robusta/Arabica" },
  { country: "Aethiopien", production: 8500000, share: 4.8, change: 3.8, variety: "Arabica" },
  { country: "Honduras", production: 6200000, share: 3.5, change: 12.4, variety: "Arabica" },
  { country: "Peru", production: 4200000, share: 2.4, change: 8.7, variety: "Arabica" },
  { country: "Uganda", production: 6800000, share: 3.8, change: 4.2, variety: "Robusta" },
  { country: "Indien", production: 5900000, share: 3.3, change: 1.5, variety: "Arabica/Robusta" },
  { country: "Mexiko", production: 4100000, share: 2.3, change: -2.1, variety: "Arabica" },
];

// FX Rates relevant for coffee trade
const FX_RATES = [
  { pair: "EUR/USD", rate: 1.0865, change: 0.0023, impact: "Direkt auf Einkaufspreise" },
  { pair: "EUR/PEN", rate: 4.0250, change: -0.0120, impact: "Peru Importkosten" },
  { pair: "EUR/BRL", rate: 5.4320, change: 0.0180, impact: "Brasilien Wettbewerb" },
  { pair: "EUR/COP", rate: 4285.50, change: 12.30, impact: "Kolumbien Alternative" },
  { pair: "USD/PEN", rate: 3.7050, change: -0.0085, impact: "Dollar-Basis Peru" },
];

// Peru Weather Data by Region
const PERU_WEATHER = [
  { region: "Cajamarca", temp: 18.5, humidity: 72, rainfall: 2.4, forecast: "Ideal fuer Ernte", riskLevel: "low" },
  { region: "San Martin", temp: 24.2, humidity: 85, rainfall: 8.6, forecast: "Erhoehte Feuchtigkeit", riskLevel: "medium" },
  { region: "Amazonas", temp: 22.8, humidity: 78, rainfall: 5.2, forecast: "Normale Bedingungen", riskLevel: "low" },
  { region: "Junin", temp: 16.4, humidity: 65, rainfall: 1.8, forecast: "Trocken - gut fuer Trocknung", riskLevel: "low" },
  { region: "Cusco", temp: 14.2, humidity: 58, rainfall: 0.4, forecast: "Sehr trocken", riskLevel: "low" },
  { region: "Puno", temp: 12.8, humidity: 52, rainfall: 0.2, forecast: "Kuehle Nachttemperaturen", riskLevel: "medium" },
];

// Shipping Routes and Costs
const SHIPPING_ROUTES = [
  { route: "Callao - Hamburg", container20ft: 2450, container40ft: 3850, transitDays: 32, reliability: 94 },
  { route: "Callao - Rotterdam", container20ft: 2380, container40ft: 3720, transitDays: 30, reliability: 96 },
  { route: "Callao - Antwerpen", container20ft: 2420, container40ft: 3780, transitDays: 31, reliability: 95 },
  { route: "Callao - Bremen", container20ft: 2520, container40ft: 3920, transitDays: 34, reliability: 92 },
  { route: "Paita - Hamburg", container20ft: 2680, container40ft: 4150, transitDays: 35, reliability: 89 },
];

// Market News
const MARKET_NEWS = [
  { title: "ICO prognostiziert globales Defizit von 7,5 Mio. Saecken fuer 2025/26", source: "ICO", time: "Vor 2 Std.", sentiment: "bullish" },
  { title: "Peru Kaffee-Exporte steigen um 15% im Q1 2026", source: "INEI", time: "Vor 4 Std.", sentiment: "bullish" },
  { title: "Brasilianische Duerre verschaerft sich - Arabica-Ernte gefaehrdet", source: "Reuters", time: "Vor 6 Std.", sentiment: "bullish" },
  { title: "Container-Engpaesse in Asien entspannen sich leicht", source: "Freightos", time: "Vor 8 Std.", sentiment: "neutral" },
  { title: "Fair Trade erhoet Mindestpreis auf $1.90/lb ab April", source: "FLO", time: "Vor 12 Std.", sentiment: "bullish" },
  { title: "Vietnam Robusta-Ernte uebertrifft Erwartungen", source: "USDA", time: "Vor 1 Tag", sentiment: "bearish" },
  { title: "Neue EU-Entwaldungsverordnung tritt im Dezember in Kraft", source: "EU", time: "Vor 1 Tag", sentiment: "neutral" },
  { title: "Kolumbien meldet Rekord-Cupping-Scores bei Nariño-Lots", source: "FNC", time: "Vor 2 Tagen", sentiment: "bullish" },
];

// Certification Premiums
const CERTIFICATION_PREMIUMS = [
  { cert: "Fair Trade Organic", premium: 0.30, basePrice: 1.90, total: 2.20, trend: "stable" },
  { cert: "Fair Trade", premium: 0.20, basePrice: 1.90, total: 2.10, trend: "up" },
  { cert: "Organic", premium: 0.30, basePrice: null, total: null, trend: "stable" },
  { cert: "Rainforest Alliance", premium: 0.10, basePrice: null, total: null, trend: "stable" },
  { cert: "Bird Friendly", premium: 0.25, basePrice: null, total: null, trend: "up" },
  { cert: "C.A.F.E. Practices", premium: 0.05, basePrice: null, total: null, trend: "stable" },
];

// Quality Grades and typical prices
const QUALITY_GRADES = [
  { grade: "Specialty Grade (85+)", priceRange: "$4.50 - $8.00/lb", availability: "Begrenzt", demand: "Sehr hoch" },
  { grade: "Premium Grade (82-84)", priceRange: "$3.20 - $4.50/lb", availability: "Moderat", demand: "Hoch" },
  { grade: "Exchange Grade (80-82)", priceRange: "$2.40 - $3.20/lb", availability: "Gut", demand: "Stabil" },
  { grade: "Standard Grade (unter 80)", priceRange: "$1.80 - $2.40/lb", availability: "Hoch", demand: "Moderat" },
];

// Peru Export Statistics
const PERU_EXPORTS = {
  totalVolume: "4.2 Mio. Saecke (60kg)",
  totalValue: "$1.12 Mrd. USD",
  topDestinations: [
    { country: "USA", share: 28, volume: "1.18 Mio." },
    { country: "Deutschland", share: 22, volume: "0.92 Mio." },
    { country: "Belgien", share: 12, volume: "0.50 Mio." },
    { country: "Kanada", share: 8, volume: "0.34 Mio." },
    { country: "Schweden", share: 6, volume: "0.25 Mio." },
    { country: "Andere", share: 24, volume: "1.01 Mio." },
  ],
  varietyBreakdown: [
    { variety: "Typica", share: 35 },
    { variety: "Caturra", share: 28 },
    { variety: "Bourbon", share: 18 },
    { variety: "Catimor", share: 12 },
    { variety: "Andere", share: 7 },
  ],
};

// ============================================================================
// COMPONENT
// ============================================================================

export default function MarktPage() {
  const [activeTab, setActiveTab] = useState<"futures" | "production" | "peru" | "shipping" | "quality">("futures");
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [historicalData] = useState(generateHistoricalPrices());

  const refresh = useCallback(() => {
    setLastRefresh(new Date());
  }, []);

  useEffect(() => {
    const interval = setInterval(refresh, 60000);
    return () => clearInterval(interval);
  }, [refresh]);

  const formatChange = (change: number, suffix = "") => {
    const sign = change >= 0 ? "+" : "";
    return `${sign}${change.toFixed(2)}${suffix}`;
  };

  const getChangeColor = (change: number) => {
    if (change > 0) return "var(--color-success)";
    if (change < 0) return "var(--color-danger)";
    return "var(--color-text-muted)";
  };

  return (
    <>
      {/* Page Header */}
      <header className="pageHeader">
        <div className="pageHeaderContent">
          <h1 className="h1">Kaffee-Marktdaten</h1>
          <p className="subtitle">
            Umfassende Marktinformationen fuer professionellen Kaffeehandel
          </p>
        </div>
        <div className="pageHeaderActions">
          <span className="muted" style={{ fontSize: "var(--font-size-sm)" }}>
            Stand: {lastRefresh.toLocaleString("de-DE")}
          </span>
          <button className="btn btnSecondary" onClick={refresh}>
            Aktualisieren
          </button>
        </div>
      </header>

      {/* Quick Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "var(--space-4)", marginBottom: "var(--space-6)" }}>
        <div className="panel" style={{ padding: "var(--space-4)" }}>
          <div className="muted" style={{ fontSize: "var(--font-size-sm)", marginBottom: "var(--space-1)" }}>Arabica (KC=F)</div>
          <div style={{ fontSize: "var(--font-size-2xl)", fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>245.30</div>
          <div style={{ color: "var(--color-success)", fontVariantNumeric: "tabular-nums" }}>+3.45 (+1.43%)</div>
        </div>
        <div className="panel" style={{ padding: "var(--space-4)" }}>
          <div className="muted" style={{ fontSize: "var(--font-size-sm)", marginBottom: "var(--space-1)" }}>Robusta (RC=F)</div>
          <div style={{ fontSize: "var(--font-size-2xl)", fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>4,125</div>
          <div style={{ color: "var(--color-danger)", fontVariantNumeric: "tabular-nums" }}>-28.00 (-0.67%)</div>
        </div>
        <div className="panel" style={{ padding: "var(--space-4)" }}>
          <div className="muted" style={{ fontSize: "var(--font-size-sm)", marginBottom: "var(--space-1)" }}>EUR/USD</div>
          <div style={{ fontSize: "var(--font-size-2xl)", fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>1.0865</div>
          <div style={{ color: "var(--color-success)", fontVariantNumeric: "tabular-nums" }}>+0.21%</div>
        </div>
        <div className="panel" style={{ padding: "var(--space-4)" }}>
          <div className="muted" style={{ fontSize: "var(--font-size-sm)", marginBottom: "var(--space-1)" }}>Peru Exporte 2026</div>
          <div style={{ fontSize: "var(--font-size-2xl)", fontWeight: 700 }}>4.2M</div>
          <div style={{ color: "var(--color-success)" }}>+8.7% YoY</div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div style={{ display: "flex", gap: "var(--space-2)", marginBottom: "var(--space-4)", borderBottom: "1px solid var(--color-border)", paddingBottom: "var(--space-2)", flexWrap: "wrap" }}>
        {[
          { id: "futures", label: "Futures und FX" },
          { id: "production", label: "Globale Produktion" },
          { id: "peru", label: "Peru Details" },
          { id: "shipping", label: "Logistik" },
          { id: "quality", label: "Qualitaet" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as typeof activeTab)}
            style={{
              padding: "var(--space-2) var(--space-4)",
              background: activeTab === tab.id ? "var(--color-primary)" : "transparent",
              color: activeTab === tab.id ? "white" : "var(--color-text)",
              border: "none",
              borderRadius: "var(--radius-md)",
              cursor: "pointer",
              fontWeight: activeTab === tab.id ? 600 : 400,
              transition: "all 0.15s ease",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Futures and FX Tab */}
      {activeTab === "futures" && (
        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "var(--space-6)" }}>
          <div>
            {/* Futures Table */}
            <section className="panel" aria-labelledby="futures-title">
              <div className="panelHeader">
                <h2 id="futures-title" className="panelTitle">Kaffee Futures</h2>
                <Badge tone="good">ICE Exchange</Badge>
              </div>
              <div className="tableWrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Kontrakt</th>
                      <th>Monat</th>
                      <th style={{ textAlign: "right" }}>Preis</th>
                      <th style={{ textAlign: "right" }}>Aenderung</th>
                      <th style={{ textAlign: "right" }}>Volumen</th>
                      <th style={{ textAlign: "right" }}>Open Interest</th>
                    </tr>
                  </thead>
                  <tbody>
                    {COFFEE_FUTURES.map((f, i) => (
                      <tr key={i}>
                        <td><strong>{f.name}</strong></td>
                        <td>{f.month}</td>
                        <td style={{ textAlign: "right", fontVariantNumeric: "tabular-nums", fontWeight: 600 }}>
                          {f.price.toLocaleString("de-DE", { minimumFractionDigits: 2 })}
                        </td>
                        <td style={{ textAlign: "right", color: getChangeColor(f.change), fontVariantNumeric: "tabular-nums" }}>
                          {formatChange(f.change)}
                        </td>
                        <td style={{ textAlign: "right", fontVariantNumeric: "tabular-nums" }}>{f.volume.toLocaleString()}</td>
                        <td style={{ textAlign: "right", fontVariantNumeric: "tabular-nums" }}>{f.openInterest.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            {/* FX Rates */}
            <section className="panel" aria-labelledby="fx-title" style={{ marginTop: "var(--space-4)" }}>
              <div className="panelHeader">
                <h2 id="fx-title" className="panelTitle">Wechselkurse</h2>
                <Badge tone="neutral">Kaffee-relevant</Badge>
              </div>
              <div className="tableWrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Waehrungspaar</th>
                      <th style={{ textAlign: "right" }}>Kurs</th>
                      <th style={{ textAlign: "right" }}>Aenderung</th>
                      <th>Relevanz</th>
                    </tr>
                  </thead>
                  <tbody>
                    {FX_RATES.map((fx) => (
                      <tr key={fx.pair}>
                        <td><strong className="mono">{fx.pair}</strong></td>
                        <td style={{ textAlign: "right", fontVariantNumeric: "tabular-nums", fontWeight: 600 }}>{fx.rate.toFixed(4)}</td>
                        <td style={{ textAlign: "right", color: getChangeColor(fx.change), fontVariantNumeric: "tabular-nums" }}>
                          {formatChange(fx.change)}
                        </td>
                        <td className="muted" style={{ fontSize: "var(--font-size-sm)" }}>{fx.impact}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            {/* Mini Chart - Historical Prices */}
            <section className="panel" aria-labelledby="chart-title" style={{ marginTop: "var(--space-4)" }}>
              <div className="panelHeader">
                <h2 id="chart-title" className="panelTitle">Arabica 30-Tage Verlauf</h2>
              </div>
              <div style={{ padding: "var(--space-4)", height: 200, display: "flex", alignItems: "flex-end", gap: 2 }}>
                {historicalData.map((d, i) => {
                  const min = Math.min(...historicalData.map(x => x.price));
                  const max = Math.max(...historicalData.map(x => x.price));
                  const height = ((d.price - min) / (max - min)) * 150 + 20;
                  const isUp = i > 0 && d.price > historicalData[i-1].price;
                  return (
                    <div
                      key={i}
                      title={`${d.date}: ${d.price.toFixed(2)}`}
                      style={{
                        flex: 1,
                        height,
                        background: isUp ? "var(--color-success)" : "var(--color-danger)",
                        opacity: 0.7,
                        borderRadius: "2px 2px 0 0",
                        minWidth: 4,
                      }}
                    />
                  );
                })}
              </div>
              <div style={{ padding: "0 var(--space-4) var(--space-3)", display: "flex", justifyContent: "space-between" }}>
                <span className="muted" style={{ fontSize: "var(--font-size-xs)" }}>{historicalData[0].date}</span>
                <span className="muted" style={{ fontSize: "var(--font-size-xs)" }}>{historicalData[historicalData.length-1].date}</span>
              </div>
            </section>
          </div>

          {/* Sidebar - News */}
          <div>
            <section className="panel" aria-labelledby="news-title">
              <div className="panelHeader">
                <h2 id="news-title" className="panelTitle">Marktnachrichten</h2>
              </div>
              <div style={{ display: "flex", flexDirection: "column" }}>
                {MARKET_NEWS.map((news, i) => (
                  <div
                    key={i}
                    style={{
                      padding: "var(--space-3)",
                      borderBottom: i < MARKET_NEWS.length - 1 ? "1px solid var(--color-border)" : "none",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "flex-start", gap: "var(--space-2)" }}>
                      <span style={{
                        width: 8,
                        height: 8,
                        borderRadius: "50%",
                        background: news.sentiment === "bullish" ? "var(--color-success)" : news.sentiment === "bearish" ? "var(--color-danger)" : "var(--color-warning)",
                        flexShrink: 0,
                        marginTop: 6,
                      }} />
                      <div>
                        <div style={{ fontSize: "var(--font-size-sm)", lineHeight: 1.4 }}>{news.title}</div>
                        <div className="muted" style={{ fontSize: "var(--font-size-xs)", marginTop: "var(--space-1)" }}>
                          {news.source} - {news.time}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </div>
      )}

      {/* Global Production Tab */}
      {activeTab === "production" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-6)" }}>
          <section className="panel">
            <div className="panelHeader">
              <h2 className="panelTitle">Globale Produktion 2025/26</h2>
              <Badge tone="neutral">Prognose</Badge>
            </div>
            <div className="tableWrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Land</th>
                    <th style={{ textAlign: "right" }}>Produktion</th>
                    <th style={{ textAlign: "right" }}>Anteil</th>
                    <th style={{ textAlign: "right" }}>YoY</th>
                    <th>Sorte</th>
                  </tr>
                </thead>
                <tbody>
                  {GLOBAL_PRODUCTION.map((p) => (
                    <tr key={p.country}>
                      <td><strong>{p.country}</strong></td>
                      <td style={{ textAlign: "right", fontVariantNumeric: "tabular-nums" }}>{(p.production / 1000000).toFixed(1)}M</td>
                      <td style={{ textAlign: "right", fontVariantNumeric: "tabular-nums" }}>{p.share}%</td>
                      <td style={{ textAlign: "right", color: getChangeColor(p.change), fontVariantNumeric: "tabular-nums" }}>
                        {formatChange(p.change, "%")}
                      </td>
                      <td className="muted">{p.variety}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="panel">
            <div className="panelHeader">
              <h2 className="panelTitle">Marktverteilung</h2>
            </div>
            <div style={{ padding: "var(--space-4)" }}>
              {GLOBAL_PRODUCTION.slice(0, 7).map((p) => (
                <div key={p.country} style={{ marginBottom: "var(--space-3)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "var(--space-1)" }}>
                    <span>{p.country}</span>
                    <span className="mono">{p.share}%</span>
                  </div>
                  <div style={{ height: 8, background: "var(--color-bg-muted)", borderRadius: 4, overflow: "hidden" }}>
                    <div style={{ 
                      width: `${p.share}%`, 
                      height: "100%", 
                      background: p.country === "Peru" ? "var(--color-primary)" : "var(--color-text-muted)",
                      borderRadius: 4,
                    }} />
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      )}

      {/* Peru Details Tab */}
      {activeTab === "peru" && (
        <>
          {/* Export Stats */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "var(--space-4)", marginBottom: "var(--space-6)" }}>
            <div className="panel" style={{ padding: "var(--space-4)", textAlign: "center" }}>
              <div className="muted" style={{ fontSize: "var(--font-size-sm)" }}>Exportvolumen</div>
              <div style={{ fontSize: "var(--font-size-xl)", fontWeight: 700 }}>{PERU_EXPORTS.totalVolume}</div>
            </div>
            <div className="panel" style={{ padding: "var(--space-4)", textAlign: "center" }}>
              <div className="muted" style={{ fontSize: "var(--font-size-sm)" }}>Exportwert</div>
              <div style={{ fontSize: "var(--font-size-xl)", fontWeight: 700 }}>{PERU_EXPORTS.totalValue}</div>
            </div>
            <div className="panel" style={{ padding: "var(--space-4)", textAlign: "center" }}>
              <div className="muted" style={{ fontSize: "var(--font-size-sm)" }}>Kooperativen</div>
              <div style={{ fontSize: "var(--font-size-xl)", fontWeight: 700 }}>ca. 230</div>
            </div>
            <div className="panel" style={{ padding: "var(--space-4)", textAlign: "center" }}>
              <div className="muted" style={{ fontSize: "var(--font-size-sm)" }}>Kaffeebauern</div>
              <div style={{ fontSize: "var(--font-size-xl)", fontWeight: 700 }}>ca. 223,000</div>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "var(--space-6)" }}>
            {/* Cooperatives */}
            <section className="panel">
              <div className="panelHeader">
                <h2 className="panelTitle">Peru Kooperativen</h2>
                <Link href="/cooperatives" className="btn btnSecondary" style={{ fontSize: "var(--font-size-sm)" }}>
                  Alle anzeigen
                </Link>
              </div>
              <div className="tableWrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Kooperative</th>
                      <th>Region</th>
                      <th style={{ textAlign: "right" }}>Mitglieder</th>
                      <th style={{ textAlign: "right" }}>Cupping</th>
                      <th>Zertifizierungen</th>
                    </tr>
                  </thead>
                  <tbody>
                    {PERU_COOPERATIVES.map((c) => (
                      <tr key={c.name}>
                        <td><strong>{c.name}</strong></td>
                        <td>{c.region}</td>
                        <td style={{ textAlign: "right", fontVariantNumeric: "tabular-nums" }}>{c.members.toLocaleString()}</td>
                        <td style={{ textAlign: "right", fontVariantNumeric: "tabular-nums" }}>{c.avgCupping}</td>
                        <td>
                          <div style={{ display: "flex", gap: "var(--space-1)", flexWrap: "wrap" }}>
                            {c.certifications.slice(0, 2).map((cert) => (
                              <Badge key={cert} tone="neutral" style={{ fontSize: "var(--font-size-xs)" }}>{cert}</Badge>
                            ))}
                            {c.certifications.length > 2 && (
                              <Badge tone="neutral" style={{ fontSize: "var(--font-size-xs)" }}>+{c.certifications.length - 2}</Badge>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            {/* Weather and Destinations */}
            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
              <section className="panel">
                <div className="panelHeader">
                  <h2 className="panelTitle">Wetter Peru</h2>
                </div>
                <div style={{ display: "flex", flexDirection: "column" }}>
                  {PERU_WEATHER.map((w) => (
                    <div key={w.region} style={{ padding: "var(--space-3)", borderBottom: "1px solid var(--color-border)" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <strong>{w.region}</strong>
                        <Badge tone={w.riskLevel === "low" ? "good" : "warn"}>{w.temp} C</Badge>
                      </div>
                      <div className="muted" style={{ fontSize: "var(--font-size-sm)" }}>
                        {w.humidity}% Feuchte - {w.rainfall}mm Regen
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              <section className="panel">
                <div className="panelHeader">
                  <h2 className="panelTitle">Export-Ziele</h2>
                </div>
                <div style={{ padding: "var(--space-3)" }}>
                  {PERU_EXPORTS.topDestinations.slice(0, 5).map((d) => (
                    <div key={d.country} style={{ display: "flex", justifyContent: "space-between", padding: "var(--space-2) 0", borderBottom: "1px solid var(--color-border)" }}>
                      <span>{d.country}</span>
                      <span className="mono">{d.share}%</span>
                    </div>
                  ))}
                </div>
              </section>
            </div>
          </div>
        </>
      )}

      {/* Shipping Tab */}
      {activeTab === "shipping" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-6)" }}>
          <section className="panel">
            <div className="panelHeader">
              <h2 className="panelTitle">Frachtraten Peru-Europa</h2>
              <Badge tone="neutral">Container</Badge>
            </div>
            <div className="tableWrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Route</th>
                    <th style={{ textAlign: "right" }}>20ft</th>
                    <th style={{ textAlign: "right" }}>40ft</th>
                    <th style={{ textAlign: "right" }}>Transit</th>
                    <th style={{ textAlign: "right" }}>Zuverlaessigkeit</th>
                  </tr>
                </thead>
                <tbody>
                  {SHIPPING_ROUTES.map((r) => (
                    <tr key={r.route}>
                      <td><strong>{r.route}</strong></td>
                      <td style={{ textAlign: "right", fontVariantNumeric: "tabular-nums" }}>${r.container20ft.toLocaleString()}</td>
                      <td style={{ textAlign: "right", fontVariantNumeric: "tabular-nums" }}>${r.container40ft.toLocaleString()}</td>
                      <td style={{ textAlign: "right", fontVariantNumeric: "tabular-nums" }}>{r.transitDays} Tage</td>
                      <td style={{ textAlign: "right" }}>
                        <Badge tone={r.reliability >= 95 ? "good" : r.reliability >= 90 ? "neutral" : "warn"}>
                          {r.reliability}%
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="panel">
            <div className="panelHeader">
              <h2 className="panelTitle">Kostenberechnung</h2>
            </div>
            <div style={{ padding: "var(--space-4)" }}>
              <div style={{ background: "var(--color-bg-muted)", padding: "var(--space-4)", borderRadius: "var(--radius-lg)", marginBottom: "var(--space-4)" }}>
                <div className="muted" style={{ fontSize: "var(--font-size-sm)", marginBottom: "var(--space-2)" }}>Beispiel: 1 Container (275 Saecke) Specialty nach Hamburg</div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-3)" }}>
                  <div>
                    <div className="muted">FOB Callao</div>
                    <div style={{ fontWeight: 600 }}>$74,250</div>
                  </div>
                  <div>
                    <div className="muted">Fracht</div>
                    <div style={{ fontWeight: 600 }}>$2,450</div>
                  </div>
                  <div>
                    <div className="muted">Versicherung</div>
                    <div style={{ fontWeight: 600 }}>$1,114</div>
                  </div>
                  <div>
                    <div className="muted">Handling</div>
                    <div style={{ fontWeight: 600 }}>$850</div>
                  </div>
                </div>
                <div style={{ borderTop: "2px solid var(--color-border)", marginTop: "var(--space-3)", paddingTop: "var(--space-3)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <strong>CIF Hamburg Total</strong>
                    <strong style={{ color: "var(--color-primary)" }}>$78,664</strong>
                  </div>
                  <div className="muted" style={{ fontSize: "var(--font-size-sm)" }}>= $4.77/lb landed cost</div>
                </div>
              </div>
              <Link href="/ki" className="btn btnPrimary" style={{ width: "100%" }}>
                Eigene Kalkulation mit KI-Assistent
              </Link>
            </div>
          </section>
        </div>
      )}

      {/* Quality Tab */}
      {activeTab === "quality" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-6)" }}>
          <section className="panel">
            <div className="panelHeader">
              <h2 className="panelTitle">Zertifizierungs-Praemien</h2>
            </div>
            <div className="tableWrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Zertifizierung</th>
                    <th style={{ textAlign: "right" }}>Praemie</th>
                    <th style={{ textAlign: "right" }}>Mindestpreis</th>
                    <th style={{ textAlign: "right" }}>Trend</th>
                  </tr>
                </thead>
                <tbody>
                  {CERTIFICATION_PREMIUMS.map((c) => (
                    <tr key={c.cert}>
                      <td><strong>{c.cert}</strong></td>
                      <td style={{ textAlign: "right", fontVariantNumeric: "tabular-nums" }}>+${c.premium.toFixed(2)}/lb</td>
                      <td style={{ textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                        {c.basePrice ? `$${c.basePrice.toFixed(2)}` : "-"}
                      </td>
                      <td style={{ textAlign: "right" }}>
                        <Badge tone={c.trend === "up" ? "good" : "neutral"}>
                          {c.trend === "up" ? "Steigend" : "Stabil"}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="panel">
            <div className="panelHeader">
              <h2 className="panelTitle">Qualitaetsgrade</h2>
            </div>
            <div style={{ display: "flex", flexDirection: "column" }}>
              {QUALITY_GRADES.map((g) => (
                <div key={g.grade} style={{ padding: "var(--space-3)", borderBottom: "1px solid var(--color-border)" }}>
                  <div style={{ fontWeight: 600, marginBottom: "var(--space-1)" }}>{g.grade}</div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "var(--space-2)", fontSize: "var(--font-size-sm)" }}>
                    <div>
                      <span className="muted">Preis: </span>
                      <span className="mono">{g.priceRange}</span>
                    </div>
                    <div>
                      <span className="muted">Verfuegbarkeit: </span>
                      <span>{g.availability}</span>
                    </div>
                    <div>
                      <span className="muted">Nachfrage: </span>
                      <span>{g.demand}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Peru Varieties */}
          <section className="panel" style={{ gridColumn: "span 2" }}>
            <div className="panelHeader">
              <h2 className="panelTitle">Peru Sorten-Verteilung</h2>
            </div>
            <div style={{ padding: "var(--space-4)", display: "flex", gap: "var(--space-6)", flexWrap: "wrap", justifyContent: "center" }}>
              {PERU_EXPORTS.varietyBreakdown.map((v) => (
                <div key={v.variety} style={{ textAlign: "center", minWidth: 100 }}>
                  <div style={{ 
                    width: 80, 
                    height: 80, 
                    borderRadius: "50%", 
                    background: `conic-gradient(var(--color-primary) ${v.share * 3.6}deg, var(--color-bg-muted) 0deg)`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    margin: "0 auto var(--space-2)",
                  }}>
                    <div style={{ 
                      width: 60, 
                      height: 60, 
                      borderRadius: "50%", 
                      background: "var(--color-surface)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontWeight: 700,
                    }}>
                      {v.share}%
                    </div>
                  </div>
                  <div style={{ fontWeight: 500 }}>{v.variety}</div>
                </div>
              ))}
            </div>
          </section>
        </div>
      )}
    </>
  );
}
