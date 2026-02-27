"use client";

import { useEffect, useRef, useState } from "react";
import { apiFetch, apiBaseUrl, getToken } from "../../lib/api";

interface MarketPoint {
  value: number;
  unit?: string | null;
  currency?: string | null;
  observed_at: string;
}

interface MarketSnapshot {
  [key: string]: MarketPoint | null;
}

interface RealtimePrice {
  price_usd_per_lb: number;
  observed_at: string;
  source_name: string;
}

// Default reference price when live data unavailable
const FALLBACK_COFFEE_PRICE = 2.50;

// Feature flag: set NEXT_PUBLIC_REALTIME_PRICE_FEED_ENABLED=true to enable WebSocket
const REALTIME_ENABLED =
  process.env.NEXT_PUBLIC_REALTIME_PRICE_FEED_ENABLED === "true";

/** Build the WebSocket URL for the realtime price endpoint. */
function buildWsUrl(): string {
  const http = apiBaseUrl();
  const ws = http.replace(/^http/, "ws");
  const token = getToken();
  return `${ws}/market/ws/price${token ? `?token=${encodeURIComponent(token)}` : ""}`;
}

export default function MarketPriceWidget() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [market, setMarket] = useState<MarketSnapshot | null>(null);
  const [realtimePrice, setRealtimePrice] = useState<RealtimePrice | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // --- WebSocket path (when feature flag is on) ---
  useEffect(() => {
    if (!REALTIME_ENABLED) return;

    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let alive = true;

    const connect = () => {
      if (!alive) return;
      try {
        const ws = new WebSocket(buildWsUrl());
        wsRef.current = ws;

        ws.onopen = () => {
          setError(null);
          setLoading(false);
        };

        ws.onmessage = (evt) => {
          try {
            const data: RealtimePrice = JSON.parse(evt.data);
            setRealtimePrice(data);
            setLoading(false);
          } catch {
            // ignore malformed frames
          }
        };

        ws.onerror = () => {
          setError("WebSocket-Verbindungsfehler");
          setLoading(false);
        };

        ws.onclose = () => {
          if (alive) {
            // Reconnect after 5 s
            reconnectTimer = setTimeout(connect, 5000);
          }
        };
      } catch {
        setError("WebSocket nicht verfügbar");
        setLoading(false);
      }
    };

    connect();

    return () => {
      alive = false;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  // --- HTTP snapshot fetch (always used; realtime only overrides coffee price) ---
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await apiFetch<MarketSnapshot>("/market/latest");
        if (!alive) return;
        setMarket(data);
        // When realtime is enabled, loading is controlled by the WebSocket,
        // but we still need the snapshot data (e.g. EUR/USD).
        if (!REALTIME_ENABLED) setLoading(false);
      } catch (e: unknown) {
        if (!alive) return;
        setError(e instanceof Error ? e.message : String(e));
        if (!REALTIME_ENABLED) setLoading(false);
      }
    })();

    return () => {
      alive = false;
    };
  }, []);

  // Derive display values: realtime overrides coffee price when WS is connected;
  // HTTP snapshot provides EUR/USD and serves as coffee fallback during WS setup.
  const coffeePrice = realtimePrice
    ? { value: realtimePrice.price_usd_per_lb, observed_at: realtimePrice.observed_at }
    : (market?.["COFFEE_C:USD_LB"] ?? null);

  const eurUsd = market?.["FX:USD_EUR"] ?? null;

  const isRealtime = REALTIME_ENABLED && realtimePrice !== null;

  const formatDate = (dateStr?: string | null) => {
    if (!dateStr) return "–";
    const d = new Date(dateStr);
    return d.toLocaleString("de-DE", { dateStyle: "short", timeStyle: "short" });
  };

  return (
    <div className="panel card">
      <div className="cardLabel">
        Kaffeebörsenpreis
        {isRealtime && (
          <span
            style={{
              marginLeft: "6px",
              fontSize: "10px",
              color: "var(--good, #4caf50)",
              fontWeight: 600,
            }}
          >
            ● LIVE
          </span>
        )}
      </div>

      {error ? (
        <div style={{ fontSize: "12px", color: "var(--bad)", marginTop: "8px" }}>
          Fehler beim Laden
        </div>
      ) : loading ? (
        <div className="cardValue">…</div>
      ) : (
        <>
          <div className="cardValue">
            {coffeePrice
              ? `$${coffeePrice.value.toFixed(2)}/lb`
              : `$${FALLBACK_COFFEE_PRICE.toFixed(2)}/lb`}
          </div>
          <div className="cardHint">
            {coffeePrice
              ? `Coffee C · ${formatDate(coffeePrice.observed_at)}`
              : "Coffee C · Referenzwert"}
          </div>

          {eurUsd && (
            <div style={{ fontSize: "12px", color: "var(--muted)", marginTop: "8px" }}>
              EUR/USD: {eurUsd.value.toFixed(4)}
            </div>
          )}

          {!coffeePrice && (
            <div
              style={{
                fontSize: "11px",
                color: "var(--muted)",
                marginTop: "8px",
                fontStyle: "italic",
              }}
            >
              Keine Live-Daten · Referenzwert: ${FALLBACK_COFFEE_PRICE}/lb
            </div>
          )}
        </>
      )}
    </div>
  );
}
