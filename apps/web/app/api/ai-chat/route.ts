import {
  consumeStream,
  convertToModelMessages,
  streamText,
  tool,
  UIMessage,
} from 'ai'
import { z } from 'zod'

export const maxDuration = 30

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
    consumeSseStream: consumeStream,
  })
}
