// Server-side API route to fetch coffee prices (avoids CORS issues)
export const dynamic = 'force-dynamic'

interface YahooFinanceResponse {
  chart?: {
    result?: Array<{
      meta?: {
        regularMarketPrice?: number
        previousClose?: number
        currency?: string
        regularMarketTime?: number
      }
      indicators?: {
        quote?: Array<{
          close?: number[]
        }>
      }
    }>
  }
}

export async function GET() {
  const symbols = [
    { symbol: "KC=F", name: "ICE Coffee C Arabica Futures" },
    { symbol: "KT=F", name: "ICE Robusta Coffee Futures" },
  ]

  const results = []

  for (const { symbol, name } of symbols) {
    try {
      const response = await fetch(
        `https://query1.finance.yahoo.com/v8/finance/chart/${symbol}?interval=1d&range=5d`,
        {
          headers: {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
          },
          next: { revalidate: 300 }, // Cache for 5 minutes
        }
      )

      if (response.ok) {
        const data: YahooFinanceResponse = await response.json()
        const result = data?.chart?.result?.[0]
        const meta = result?.meta
        const quotes = result?.indicators?.quote?.[0]

        if (meta && quotes?.close) {
          const closes = quotes.close.filter((c): c is number => c !== null)
          const currentPrice = meta.regularMarketPrice || closes[closes.length - 1]
          const previousClose = meta.previousClose || closes[closes.length - 2]
          const change = currentPrice - previousClose
          const changePercent = (change / previousClose) * 100

          results.push({
            symbol,
            name,
            price: currentPrice,
            change,
            changePercent,
            currency: meta.currency || "USD",
            source: "Yahoo Finance",
            lastUpdate: meta.regularMarketTime 
              ? new Date(meta.regularMarketTime * 1000).toISOString()
              : new Date().toISOString(),
          })
        }
      }
    } catch (error) {
      console.error("Coffee price fetch failed", { symbol, error })
    }
  }

  // If no real data, return demo data
  if (results.length === 0) {
    const now = new Date().toISOString()
    results.push(
      {
        symbol: "KC=F",
        name: "ICE Coffee C Arabica Futures",
        price: 245.30 + (Math.random() - 0.5) * 10,
        change: 3.45 + (Math.random() - 0.5) * 2,
        changePercent: 1.43 + (Math.random() - 0.5) * 0.5,
        currency: "USD",
        source: "Demo (API unavailable)",
        lastUpdate: now,
      },
      {
        symbol: "KT=F",
        name: "ICE Robusta Coffee Futures",
        price: 4125.00 + (Math.random() - 0.5) * 100,
        change: -28.00 + (Math.random() - 0.5) * 20,
        changePercent: -0.67 + (Math.random() - 0.5) * 0.3,
        currency: "USD",
        source: "Demo (API unavailable)",
        lastUpdate: now,
      }
    )
  }

  return Response.json({ prices: results, timestamp: new Date().toISOString() })
}
