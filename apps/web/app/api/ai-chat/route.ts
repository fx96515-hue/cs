import {
  convertToModelMessages,
  streamText,
  tool,
  UIMessage,
} from 'ai'
import { z } from 'zod'

export const maxDuration = 60

// Coffee-specific tools for the AI assistant
const coffeeTools = {
  searchCooperatives: tool({
    description: 'Search for coffee cooperatives in Peru by region, certification, or quality score',
    inputSchema: z.object({
      region: z.string().nullable().describe('Region in Peru (e.g., Cajamarca, Junin, San Martin)'),
      certification: z.string().nullable().describe('Certification type (e.g., Fair Trade, Organic, Rainforest Alliance)'),
      minScore: z.number().nullable().describe('Minimum quality score (0-100)'),
    }),
    execute: async ({ region, certification, minScore }) => {
      // Simulated data - in production, this would query the database
      const cooperatives = [
        { name: 'Cooperativa Agraria Cafetalera Cajamarca', region: 'Cajamarca', score: 87, certifications: ['Fair Trade', 'Organic'] },
        { name: 'Sol y Cafe', region: 'Cajamarca', score: 89, certifications: ['Fair Trade', 'UTZ'] },
        { name: 'Cenfrocafe', region: 'San Martin', score: 85, certifications: ['Organic', 'Rainforest Alliance'] },
        { name: 'Cooperativa Pangoa', region: 'Junin', score: 86, certifications: ['Fair Trade'] },
        { name: 'Coopchebi', region: 'San Martin', score: 84, certifications: ['Organic'] },
      ]
      
      let filtered = cooperatives
      if (region) filtered = filtered.filter(c => c.region.toLowerCase().includes(region.toLowerCase()))
      if (certification) filtered = filtered.filter(c => c.certifications.some(cert => cert.toLowerCase().includes(certification.toLowerCase())))
      if (minScore) filtered = filtered.filter(c => c.score >= minScore)
      
      return { results: filtered, total: filtered.length }
    },
  }),

  searchRoasters: tool({
    description: 'Search for German roasteries by city or specialty focus',
    inputSchema: z.object({
      city: z.string().nullable().describe('City in Germany (e.g., Hamburg, Berlin, Munich)'),
      specialty: z.string().nullable().describe('Specialty focus (e.g., Peru, Single Origin, Direct Trade)'),
    }),
    execute: async ({ city, specialty }) => {
      const roasters = [
        { name: 'Elbgold', city: 'Hamburg', specialties: ['Single Origin', 'Direct Trade'], rating: 4.8 },
        { name: 'The Barn', city: 'Berlin', specialties: ['Single Origin', 'Peru'], rating: 4.7 },
        { name: 'Bonanza Coffee', city: 'Berlin', specialties: ['Peru', 'Direct Trade'], rating: 4.6 },
        { name: 'Man vs Machine', city: 'Munich', specialties: ['Single Origin'], rating: 4.5 },
        { name: 'Coffee Circle', city: 'Berlin', specialties: ['Direct Trade', 'Organic'], rating: 4.4 },
      ]
      
      let filtered = roasters
      if (city) filtered = filtered.filter(r => r.city.toLowerCase().includes(city.toLowerCase()))
      if (specialty) filtered = filtered.filter(r => r.specialties.some(s => s.toLowerCase().includes(specialty.toLowerCase())))
      
      return { results: filtered, total: filtered.length }
    },
  }),

  getCoffeePrices: tool({
    description: 'Get current coffee market prices and trends',
    inputSchema: z.object({
      type: z.enum(['arabica', 'robusta', 'specialty']).describe('Type of coffee'),
    }),
    execute: async ({ type }) => {
      const prices: Record<string, { price: number; unit: string; trend: string; change: number }> = {
        arabica: { price: 2.45, unit: 'USD/lb', trend: 'up', change: 3.2 },
        robusta: { price: 1.85, unit: 'USD/lb', trend: 'stable', change: 0.5 },
        specialty: { price: 4.80, unit: 'USD/lb', trend: 'up', change: 5.1 },
      }
      return prices[type] || prices.arabica
    },
  }),

  getWeatherForecast: tool({
    description: 'Get weather forecast for coffee growing regions in Peru',
    inputSchema: z.object({
      region: z.string().describe('Peru coffee region (Cajamarca, Junin, San Martin, Cusco, Amazonas, Puno)'),
    }),
    execute: async ({ region }) => {
      const forecasts: Record<string, { temp: number; humidity: number; rainfall: string; harvestImpact: string }> = {
        'cajamarca': { temp: 18, humidity: 72, rainfall: 'moderate', harvestImpact: 'Good conditions for harvest' },
        'junin': { temp: 20, humidity: 68, rainfall: 'light', harvestImpact: 'Excellent drying conditions' },
        'san martin': { temp: 24, humidity: 80, rainfall: 'heavy', harvestImpact: 'Risk of moisture damage' },
        'cusco': { temp: 16, humidity: 65, rainfall: 'light', harvestImpact: 'Optimal processing weather' },
        'amazonas': { temp: 22, humidity: 78, rainfall: 'moderate', harvestImpact: 'Standard conditions' },
        'puno': { temp: 14, humidity: 55, rainfall: 'none', harvestImpact: 'Dry, good for storage' },
      }
      const key = region.toLowerCase()
      return forecasts[key] || { temp: 20, humidity: 70, rainfall: 'unknown', harvestImpact: 'No data available' }
    },
  }),

  getMarketNews: tool({
    description: 'Get latest coffee market news and analysis',
    inputSchema: z.object({
      topic: z.string().nullable().describe('Specific topic (e.g., prices, harvest, exports)'),
    }),
    execute: async ({ topic }) => {
      const news = [
        { title: 'Peru Kaffee-Exporte steigen um 15%', date: '2026-03-12', summary: 'Die peruanischen Kaffee-Exporte verzeichnen ein starkes Wachstum im ersten Quartal.' },
        { title: 'ICE Coffee C Futures erreichen 3-Jahres-Hoch', date: '2026-03-10', summary: 'Globale Versorgungsengpaesse treiben die Preise weiter nach oben.' },
        { title: 'Neue Fair-Trade-Standards angekuendigt', date: '2026-03-08', summary: 'Fair Trade International aktualisiert Mindestpreise fuer 2026.' },
        { title: 'Wetterbedingungen in Cajamarca optimal', date: '2026-03-05', summary: 'Ideale Erntebedingungen erwarten Kooperativen in Nordperu.' },
      ]
      
      if (topic) {
        return news.filter(n => 
          n.title.toLowerCase().includes(topic.toLowerCase()) || 
          n.summary.toLowerCase().includes(topic.toLowerCase())
        ).slice(0, 3)
      }
      return news.slice(0, 4)
    },
  }),

  analyzeMarketTrends: tool({
    description: 'Analyze coffee market trends and provide insights',
    inputSchema: z.object({
      timeframe: z.enum(['week', 'month', 'quarter', 'year']).describe('Analysis timeframe'),
      focus: z.string().nullable().describe('Specific focus area (prices, supply, demand, quality)'),
    }),
    execute: async ({ timeframe, focus }) => {
      const trends = {
        prices: {
          direction: 'up',
          change: timeframe === 'week' ? 2.3 : timeframe === 'month' ? 8.5 : 15.2,
          drivers: ['Brasilianische Duerre', 'Steigende Nachfrage in Asien', 'USD-Schwaechung'],
          outlook: 'Preise bleiben voraussichtlich hoch bis Q3 2026',
        },
        supply: {
          status: 'tight',
          peruProduction: '4.2 Mio. Saecke (Prognose)',
          globalStock: 'Unter 5-Jahres-Durchschnitt',
          bottlenecks: ['Containerknappheit', 'Hafenverzoegerungen Callao'],
        },
        demand: {
          growth: '4.2% YoY',
          topMarkets: ['Deutschland +6%', 'USA +3%', 'Japan +5%'],
          specialty: 'Specialty-Segment waechst 12% schneller als Commodity',
        },
        quality: {
          avgCupping: 84.5,
          trend: 'Leicht steigend durch bessere Verarbeitungsmethoden',
          premiums: 'Fair Trade Premium +$0.20/lb',
        },
      }
      
      if (focus && trends[focus as keyof typeof trends]) {
        return { timeframe, focus, data: trends[focus as keyof typeof trends] }
      }
      return { timeframe, overview: trends }
    },
  }),

  calculateLandedCost: tool({
    description: 'Calculate estimated landed cost for coffee shipments',
    inputSchema: z.object({
      origin: z.string().describe('Origin region in Peru'),
      destination: z.string().describe('Destination city in Germany'),
      quantity: z.number().describe('Quantity in kg'),
      quality: z.enum(['standard', 'specialty', 'premium']).describe('Quality grade'),
    }),
    execute: async ({ origin, destination, quantity, quality }) => {
      const basePrices = { standard: 3.20, specialty: 4.80, premium: 6.50 } // EUR/kg
      const freightPerKg = 0.45 // EUR/kg average
      const insuranceRate = 0.015 // 1.5%
      const customsDuty = 0 // Coffee is duty-free in EU
      
      const fobPrice = basePrices[quality] * quantity
      const freight = freightPerKg * quantity
      const insurance = fobPrice * insuranceRate
      const handling = quantity > 1000 ? 150 : 80
      
      const total = fobPrice + freight + insurance + handling
      
      return {
        origin,
        destination,
        quantity: `${quantity} kg`,
        breakdown: {
          fobPrice: `EUR ${fobPrice.toFixed(2)}`,
          freight: `EUR ${freight.toFixed(2)}`,
          insurance: `EUR ${insurance.toFixed(2)}`,
          handling: `EUR ${handling.toFixed(2)}`,
        },
        totalLandedCost: `EUR ${total.toFixed(2)}`,
        perKg: `EUR ${(total / quantity).toFixed(2)}/kg`,
        estimatedDelivery: '4-6 Wochen ab Buchung',
      }
    },
  }),

  getDataPipelineStatus: tool({
    description: 'Get status of data collection pipeline and sources',
    inputSchema: z.object({
      source: z.string().nullable().describe('Specific data source to check (optional)'),
    }),
    execute: async ({ source }) => {
      const sources = [
        { name: 'Yahoo Finance', status: 'online', lastSync: '2026-03-14 09:00', records: 15420 },
        { name: 'ECB FX Rates', status: 'online', lastSync: '2026-03-14 08:30', records: 8920 },
        { name: 'OpenMeteo Weather', status: 'online', lastSync: '2026-03-14 06:00', records: 45600 },
        { name: 'NewsAPI', status: 'online', lastSync: '2026-03-14 07:15', records: 2340 },
        { name: 'AIS Shipping', status: 'degraded', lastSync: '2026-03-14 05:45', records: 12800 },
        { name: 'INEI Peru Stats', status: 'online', lastSync: '2026-03-13 00:00', records: 890 },
      ]
      
      if (source) {
        const found = sources.find(s => s.name.toLowerCase().includes(source.toLowerCase()))
        return found || { error: `Quelle "${source}" nicht gefunden` }
      }
      
      return {
        totalSources: sources.length,
        online: sources.filter(s => s.status === 'online').length,
        degraded: sources.filter(s => s.status === 'degraded').length,
        sources,
      }
    },
  }),

  getMLPrediction: tool({
    description: 'Get ML model predictions for freight or price forecasting',
    inputSchema: z.object({
      model: z.enum(['freight', 'price']).describe('Which model to use'),
      params: z.object({
        route: z.string().nullable().describe('Shipping route (for freight model)'),
        origin: z.string().nullable().describe('Coffee origin region (for price model)'),
        quality: z.string().nullable().describe('Quality grade (for price model)'),
      }),
    }),
    execute: async ({ model, params }) => {
      if (model === 'freight') {
        return {
          model: 'FreightCostPredictor v2.1',
          route: params.route || 'Callao-Hamburg',
          prediction: {
            estimatedCost: 'EUR 2,450 - 2,680 / Container',
            confidence: 0.87,
            factors: [
              'Fuel Price Index: +12% YoY',
              'Port Congestion: Moderate',
              'Seasonal Demand: High (Q1)',
            ],
          },
          modelAccuracy: '92% (letzte 30 Tage)',
        }
      } else {
        return {
          model: 'PriceForecaster v3.0',
          origin: params.origin || 'Cajamarca',
          quality: params.quality || 'Specialty',
          prediction: {
            priceRange: 'USD 4.65 - 5.10 / lb',
            confidence: 0.84,
            factors: [
              'Supply Shortage: Bullish',
              'Quality Premium: +15%',
              'EUR/USD Trend: Neutral',
            ],
          },
          modelAccuracy: '89% (letzte 30 Tage)',
        }
      }
    },
  }),
}

export async function POST(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json()

  const result = streamText({
    model: 'openai/gpt-5-mini',
    system: `Du bist ein KI-Assistent fuer CoffeeStudio, eine B2B-Plattform fuer Specialty Coffee.
Du hilfst bei Fragen zu:
- Peruanischen Kaffee-Kooperativen und deren Zertifizierungen
- Deutschen Roestereien und Einkaufspartnern  
- Kaffeepreisen und Markttrends
- Wetterbedingungen in Anbauregionen
- Marktnachrichten und Analysen

Antworte immer auf Deutsch. Nutze die verfuegbaren Tools um aktuelle Daten abzurufen.
Sei praezise, professionell und hilfreich. Formatiere Ergebnisse uebersichtlich.`,
    messages: await convertToModelMessages(messages),
    tools: coffeeTools,
    maxSteps: 5,
    abortSignal: req.signal,
  })

  return result.toUIMessageStreamResponse({
    originalMessages: messages,
  })
}
