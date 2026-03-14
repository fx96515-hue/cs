"use client";

import { useCallback, useEffect, useState } from "react";
import Badge from "../components/Badge";

// Types for market data
interface CoffeePrice {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  currency: string;
  source: string;
  lastUpdate: string;
}

interface FXRate {
  pair: string;
  rate: number;
  change: number;
  source: string;
}

interface WeatherData {
  region: string;
  temp: number;
  humidity: number;
  rainfall: number;
  condition: string;
}

interface NewsItem {
  title: string;
  source: string;
  url: string;
  publishedAt: string;
  sentiment: "positive" | "neutral" | "negative";
}

// Fetch coffee prices from Yahoo Finance (public API)
async function fetchCoffeePrices(): Promise<CoffeePrice[]> {
  const symbols = [
    { symbol: "KC=F", name: "ICE Coffee C Arabica Futures" },
    { symbol: "KT=F", name: "ICE Robusta Coffee Futures" },
  ];

  const results: CoffeePrice[] = [];

  for (const { symbol, name } of symbols) {
    try {
      // Yahoo Finance public API
      const response = await fetch(
        `https://query1.finance.yahoo.com/v8/finance/chart/${symbol}?interval=1d&range=2d`,
        {
          headers: { "User-Agent": "CoffeeStudio/1.0" },
          cache: "no-store",
        }
      );

      if (response.ok) {
        const data = await response.json();
        const result = data?.chart?.result?.[0];
        const meta = result?.meta;
        const quotes = result?.indicators?.quote?.[0];

        if (meta && quotes) {
          const currentPrice = meta.regularMarketPrice || quotes.close?.[quotes.close.length - 1];
          const previousClose = meta.previousClose || quotes.close?.[quotes.close.length - 2];
          const change = currentPrice - previousClose;
          const changePercent = (change / previousClose) * 100;

          results.push({
            symbol,
            name,
            price: currentPrice,
            change,
            changePercent,
            currency: meta.currency || "USD",
            source: "Yahoo Finance",
            lastUpdate: new Date(meta.regularMarketTime * 1000).toLocaleString("de-DE"),
          });
        }
      }
    } catch (error) {
      console.error(`Failed to fetch ${symbol}:`, error);
    }
  }

  // Add fallback demo data if no real data
  if (results.length === 0) {
    results.push(
      {
        symbol: "KC=F",
        name: "ICE Coffee C Arabica Futures",
        price: 245.30,
        change: 3.45,
        changePercent: 1.43,
        currency: "USD",
        source: "Demo",
        lastUpdate: new Date().toLocaleString("de-DE"),
      },
      {
        symbol: "KT=F",
        name: "ICE Robusta Coffee Futures",
        price: 4125.00,
        change: -28.00,
        changePercent: -0.67,
        currency: "USD",
        source: "Demo",
        lastUpdate: new Date().toLocaleString("de-DE"),
      }
    );
  }

  return results;
}

// Fetch FX rates from ECB (public API)
async function fetchFXRates(): Promise<FXRate[]> {
  try {
    // ECB Statistical Data Warehouse API (public, no key required)
    const response = await fetch(
      "https://data-api.ecb.europa.eu/service/data/EXR/D.USD+PEN+BRL+GBP.EUR.SP00.A?lastNObservations=2&format=jsondata",
      { cache: "no-store" }
    );

    if (response.ok) {
      const data = await response.json();
      const rates: FXRate[] = [];

      // Parse ECB SDMX-JSON format
      const series = data?.dataSets?.[0]?.series;
      const dimensions = data?.structure?.dimensions?.series;

      if (series && dimensions) {
        const currencyDim = dimensions.find((d: { id: string }) => d.id === "CURRENCY");
        const currencies = currencyDim?.values || [];

        Object.entries(series).forEach(([key, seriesData]: [string, unknown]) => {
          const keyParts = key.split(":");
          const currencyIndex = parseInt(keyParts[1]);
          const currency = currencies[currencyIndex]?.id;

          const typedSeriesData = seriesData as { observations?: Record<string, number[]> };
          const observations = typedSeriesData?.observations;
          if (observations) {
            const obsKeys = Object.keys(observations).sort();
            const latestObs = observations[obsKeys[obsKeys.length - 1]];
            const prevObs = observations[obsKeys[obsKeys.length - 2]] || latestObs;

            if (latestObs && currency) {
              const rate = latestObs[0];
              const prevRate = prevObs[0];
              rates.push({
                pair: `EUR/${currency}`,
                rate,
                change: rate - prevRate,
                source: "ECB",
              });
            }
          }
        });
      }

      if (rates.length > 0) return rates;
    }
  } catch (error) {
    console.error("Failed to fetch ECB rates:", error);
  }

  // Fallback demo data
  return [
    { pair: "EUR/USD", rate: 1.0865, change: 0.0023, source: "Demo" },
    { pair: "EUR/PEN", rate: 4.0250, change: -0.0120, source: "Demo" },
    { pair: "EUR/BRL", rate: 5.4320, change: 0.0180, source: "Demo" },
    { pair: "EUR/GBP", rate: 0.8590, change: -0.0015, source: "Demo" },
  ];
}

// Fetch weather for Peru coffee regions from Open-Meteo (public API)
async function fetchWeather(): Promise<WeatherData[]> {
  const regions = [
    { name: "Cajamarca", lat: -7.1638, lon: -78.5003 },
    { name: "San Martin", lat: -6.4858, lon: -76.3658 },
    { name: "Amazonas", lat: -5.9393, lon: -78.1128 },
    { name: "Junin", lat: -11.1589, lon: -75.9931 },
    { name: "Cusco", lat: -13.5319, lon: -71.9675 },
  ];

  const results: WeatherData[] = [];

  for (const region of regions) {
    try {
      // Open-Meteo is completely free, no API key needed
      const response = await fetch(
        `https://api.open-meteo.com/v1/forecast?latitude=${region.lat}&longitude=${region.lon}&current=temperature_2m,relative_humidity_2m,precipitation,weather_code`,
        { cache: "no-store" }
      );

      if (response.ok) {
        const data = await response.json();
        const current = data?.current;

        if (current) {
          const weatherCodes: Record<number, string> = {
            0: "Klar",
            1: "Ueberwiegend klar",
            2: "Teilweise bewoelkt",
            3: "Bewoelkt",
            45: "Nebel",
            48: "Reifnebel",
            51: "Leichter Nieselregen",
            53: "Maessiger Nieselregen",
            55: "Dichter Nieselregen",
            61: "Leichter Regen",
            63: "Maessiger Regen",
            65: "Starker Regen",
            80: "Leichte Regenschauer",
            81: "Maessige Regenschauer",
            82: "Starke Regenschauer",
            95: "Gewitter",
          };

          results.push({
            region: region.name,
            temp: current.temperature_2m,
            humidity: current.relative_humidity_2m,
            rainfall: current.precipitation,
            condition: weatherCodes[current.weather_code] || "Unbekannt",
          });
        }
      }
    } catch (error) {
      console.error(`Failed to fetch weather for ${region.name}:`, error);
    }
  }

  // Fallback if API fails
  if (results.length === 0) {
    return regions.map((r) => ({
      region: r.name,
      temp: 18 + Math.random() * 8,
      humidity: 60 + Math.random() * 25,
      rainfall: Math.random() * 5,
      condition: "Demo-Daten",
    }));
  }

  return results;
}

// Fetch coffee news (simulated - would need NewsAPI key for real data)
function getMarketNews(): NewsItem[] {
  // In production, this would call NewsAPI or similar
  return [
    {
      title: "Peru erwartet Rekordernte 2026 - Kooperativen optimistisch",
      source: "Reuters Coffee",
      url: "#",
      publishedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      sentiment: "positive",
    },
    {
      title: "ICE Arabica Futures steigen auf 3-Jahres-Hoch",
      source: "Bloomberg",
      url: "#",
      publishedAt: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
      sentiment: "positive",
    },
    {
      title: "Brasilien: Trockenheit bedroht Kaffeeernte in Minas Gerais",
      source: "Coffee Network",
      url: "#",
      publishedAt: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(),
      sentiment: "negative",
    },
    {
      title: "Containerraten stabilisieren sich nach Jahresmitte-Peak",
      source: "Freightos",
      url: "#",
      publishedAt: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
      sentiment: "neutral",
    },
    {
      title: "Fair Trade aktualisiert Mindestpreise fuer 2026",
      source: "Fair Trade International",
      url: "#",
      publishedAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      sentiment: "positive",
    },
  ];
}

export default function MarktPage() {
  const [coffeePrices, setCoffeePrices] = useState<CoffeePrice[]>([]);
  const [fxRates, setFxRates] = useState<FXRate[]>([]);
  const [weather, setWeather] = useState<WeatherData[]>([]);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadAllData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [pricesData, fxData, weatherData] = await Promise.all([
        fetchCoffeePrices(),
        fetchFXRates(),
        fetchWeather(),
      ]);

      setCoffeePrices(pricesData);
      setFxRates(fxData);
      setWeather(weatherData);
      setNews(getMarketNews());
      setLastRefresh(new Date());
    } catch (err) {
      setError("Fehler beim Laden der Marktdaten");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAllData();
    // Auto-refresh every 5 minutes
    const interval = setInterval(loadAllData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [loadAllData]);

  const formatChange = (change: number, suffix = "") => {
    const sign = change >= 0 ? "+" : "";
    return `${sign}${change.toFixed(2)}${suffix}`;
  };

  const getChangeColor = (change: number) => {
    if (change > 0) return "var(--color-success)";
    if (change < 0) return "var(--color-danger)";
    return "var(--color-text-muted)";
  };

  const getSentimentBadge = (sentiment: string) => {
    switch (sentiment) {
      case "positive":
        return <Badge tone="good">Positiv</Badge>;
      case "negative":
        return <Badge tone="bad">Negativ</Badge>;
      default:
        return <Badge tone="neutral">Neutral</Badge>;
    }
  };

  const getTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    if (diffHours < 1) return "Gerade eben";
    if (diffHours === 1) return "Vor 1 Stunde";
    if (diffHours < 24) return `Vor ${diffHours} Stunden`;
    return `Vor ${Math.floor(diffHours / 24)} Tagen`;
  };

  return (
    <>
      {/* Page Header */}
      <header className="pageHeader">
        <div className="pageHeaderContent">
          <h1 className="h1">Marktdaten Live</h1>
          <p className="subtitle">
            Echtzeitdaten aus oeffentlichen Quellen - Yahoo Finance, ECB, Open-Meteo
          </p>
        </div>
        <div className="pageHeaderActions">
          {lastRefresh && (
            <span className="muted" style={{ fontSize: "var(--font-size-sm)" }}>
              Aktualisiert: {lastRefresh.toLocaleTimeString("de-DE")}
            </span>
          )}
          <button className="btn btnPrimary" onClick={loadAllData} disabled={loading}>
            {loading ? "Laden..." : "Aktualisieren"}
          </button>
        </div>
      </header>

      {error && (
        <div className="panel" style={{ background: "var(--color-danger-subtle)", marginBottom: "var(--space-4)" }}>
          <p style={{ color: "var(--color-danger)", margin: 0 }}>{error}</p>
        </div>
      )}

      {/* Coffee Prices */}
      <section className="panel" aria-labelledby="prices-title">
        <div className="panelHeader">
          <h2 id="prices-title" className="panelTitle">
            Kaffee-Futures
          </h2>
          <Badge tone="neutral">Live von Yahoo Finance</Badge>
        </div>
        <div className="panelBody">
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "var(--space-4)" }}>
            {loading && coffeePrices.length === 0 ? (
              <div className="muted">Laden...</div>
            ) : (
              coffeePrices.map((price) => (
                <div
                  key={price.symbol}
                  style={{
                    padding: "var(--space-4)",
                    background: "var(--color-bg-muted)",
                    borderRadius: "var(--radius-lg)",
                    border: "1px solid var(--color-border)",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "var(--space-2)" }}>
                    <div>
                      <div className="mono" style={{ fontSize: "var(--font-size-sm)", color: "var(--color-text-muted)" }}>
                        {price.symbol}
                      </div>
                      <div style={{ fontWeight: 500 }}>{price.name}</div>
                    </div>
                    <Badge tone={price.source === "Demo" ? "warn" : "good"}>{price.source}</Badge>
                  </div>
                  <div style={{ display: "flex", alignItems: "baseline", gap: "var(--space-3)" }}>
                    <span style={{ fontSize: "var(--font-size-2xl)", fontWeight: 600, fontVariantNumeric: "tabular-nums" }}>
                      {price.price.toFixed(2)}
                    </span>
                    <span className="muted">{price.currency}/lb</span>
                  </div>
                  <div style={{ display: "flex", gap: "var(--space-3)", marginTop: "var(--space-2)" }}>
                    <span style={{ color: getChangeColor(price.change), fontVariantNumeric: "tabular-nums" }}>
                      {formatChange(price.change)}
                    </span>
                    <span style={{ color: getChangeColor(price.changePercent), fontVariantNumeric: "tabular-nums" }}>
                      ({formatChange(price.changePercent, "%")})
                    </span>
                  </div>
                  <div className="muted" style={{ fontSize: "var(--font-size-xs)", marginTop: "var(--space-2)" }}>
                    {price.lastUpdate}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </section>

      {/* FX Rates */}
      <section className="panel" aria-labelledby="fx-title" style={{ marginTop: "var(--space-6)" }}>
        <div className="panelHeader">
          <h2 id="fx-title" className="panelTitle">
            Wechselkurse
          </h2>
          <Badge tone="neutral">Live von ECB</Badge>
        </div>
        <div className="panelBody">
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "var(--space-4)" }}>
            {loading && fxRates.length === 0 ? (
              <div className="muted">Laden...</div>
            ) : (
              fxRates.map((fx) => (
                <div
                  key={fx.pair}
                  style={{
                    padding: "var(--space-3)",
                    background: "var(--color-bg-muted)",
                    borderRadius: "var(--radius-md)",
                    textAlign: "center",
                  }}
                >
                  <div className="mono" style={{ fontSize: "var(--font-size-sm)", color: "var(--color-text-muted)" }}>
                    {fx.pair}
                  </div>
                  <div style={{ fontSize: "var(--font-size-xl)", fontWeight: 600, fontVariantNumeric: "tabular-nums" }}>
                    {fx.rate.toFixed(4)}
                  </div>
                  <div style={{ color: getChangeColor(fx.change), fontSize: "var(--font-size-sm)", fontVariantNumeric: "tabular-nums" }}>
                    {formatChange(fx.change)}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </section>

      {/* Weather */}
      <section className="panel" aria-labelledby="weather-title" style={{ marginTop: "var(--space-6)" }}>
        <div className="panelHeader">
          <h2 id="weather-title" className="panelTitle">
            Wetter in Peru Kaffeeregionen
          </h2>
          <Badge tone="neutral">Live von Open-Meteo</Badge>
        </div>
        <div className="tableWrap">
          <table className="table">
            <thead>
              <tr>
                <th>Region</th>
                <th>Temperatur</th>
                <th>Luftfeuchtigkeit</th>
                <th>Niederschlag</th>
                <th>Bedingungen</th>
              </tr>
            </thead>
            <tbody>
              {loading && weather.length === 0 ? (
                <tr>
                  <td colSpan={5} className="muted">Laden...</td>
                </tr>
              ) : (
                weather.map((w) => (
                  <tr key={w.region}>
                    <td><strong>{w.region}</strong></td>
                    <td style={{ fontVariantNumeric: "tabular-nums" }}>{w.temp.toFixed(1)}°C</td>
                    <td style={{ fontVariantNumeric: "tabular-nums" }}>{w.humidity.toFixed(0)}%</td>
                    <td style={{ fontVariantNumeric: "tabular-nums" }}>{w.rainfall.toFixed(1)} mm</td>
                    <td>{w.condition}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Market News */}
      <section className="panel" aria-labelledby="news-title" style={{ marginTop: "var(--space-6)" }}>
        <div className="panelHeader">
          <h2 id="news-title" className="panelTitle">
            Marktnachrichten
          </h2>
          <Badge tone="warn">Simuliert</Badge>
        </div>
        <div className="panelBody">
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
            {news.map((item, idx) => (
              <div
                key={idx}
                style={{
                  padding: "var(--space-3)",
                  background: "var(--color-bg-muted)",
                  borderRadius: "var(--radius-md)",
                  borderLeft: `3px solid ${
                    item.sentiment === "positive"
                      ? "var(--color-success)"
                      : item.sentiment === "negative"
                      ? "var(--color-danger)"
                      : "var(--color-border)"
                  }`,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "var(--space-3)" }}>
                  <div>
                    <div style={{ fontWeight: 500, marginBottom: "var(--space-1)" }}>{item.title}</div>
                    <div className="muted" style={{ fontSize: "var(--font-size-sm)" }}>
                      {item.source} · {getTimeAgo(item.publishedAt)}
                    </div>
                  </div>
                  {getSentimentBadge(item.sentiment)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Data Sources Info */}
      <section className="panel" aria-labelledby="sources-title" style={{ marginTop: "var(--space-6)" }}>
        <div className="panelHeader">
          <h2 id="sources-title" className="panelTitle">
            Datenquellen
          </h2>
        </div>
        <div className="panelBody">
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "var(--space-4)" }}>
            <div>
              <h4 style={{ marginBottom: "var(--space-2)" }}>Yahoo Finance</h4>
              <p className="muted small">Kaffee-Futures (KC=F, KT=F), Echtzeit-Kurse, keine API-Key erforderlich</p>
            </div>
            <div>
              <h4 style={{ marginBottom: "var(--space-2)" }}>ECB SDMX API</h4>
              <p className="muted small">Euro-Wechselkurse (USD, PEN, BRL, GBP), taeglich aktualisiert</p>
            </div>
            <div>
              <h4 style={{ marginBottom: "var(--space-2)" }}>Open-Meteo</h4>
              <p className="muted small">Wetterdaten fuer Peru Regionen, voellig kostenlos und ohne Limits</p>
            </div>
            <div>
              <h4 style={{ marginBottom: "var(--space-2)" }}>Nachrichten</h4>
              <p className="muted small">Fuer Live-News wird ein NewsAPI-Key benoetigt (derzeit simuliert)</p>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
