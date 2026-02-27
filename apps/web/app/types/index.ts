// TypeScript types matching backend Pydantic schemas

// Multi-Country Support
export type SupportedCountry = "PE" | "CO" | "ET" | "BR";

export interface HarvestCalendar {
  main_crop_start: number;
  /** When main_crop_end < main_crop_start the harvest spans a year boundary (e.g. Oct–Feb). */
  main_crop_end: number;
  fly_crop_start?: number | null;
  fly_crop_end?: number | null;
  notes: string;
}

export interface DataSourceConfig {
  name: string;
  url: string;
  kind: string;
  reliability: number;
  description: string;
}

export interface CountryConfig {
  code: SupportedCountry;
  name: string;
  currency: string;
  currency_symbol: string;
  flag_emoji: string;
  data_source: DataSourceConfig;
  harvest_calendar: HarvestCalendar;
  ml_country_feature: string;
  default_port: string;
}

export const COUNTRY_CONFIGS: Record<SupportedCountry, CountryConfig> = {
  PE: {
    code: "PE",
    name: "Peru",
    currency: "PEN",
    currency_symbol: "S/",
    flag_emoji: "🇵🇪",
    data_source: { name: "PROMPERÚ", url: "https://www.promperu.gob.pe/", kind: "web", reliability: 0.75, description: "Peruvian export promotion agency" },
    harvest_calendar: { main_crop_start: 4, main_crop_end: 9, notes: "Main harvest April–September" },
    ml_country_feature: "PE",
    default_port: "Callao",
  },
  CO: {
    code: "CO",
    name: "Colombia",
    currency: "COP",
    currency_symbol: "COP$",
    flag_emoji: "🇨🇴",
    data_source: { name: "FNC", url: "https://federaciondecafeteros.org/", kind: "api", reliability: 0.85, description: "Federación Nacional de Cafeteros de Colombia" },
    harvest_calendar: { main_crop_start: 10, main_crop_end: 2, fly_crop_start: 4, fly_crop_end: 6, notes: "Main mitaca Oct–Feb; fly crop Apr–Jun" },
    ml_country_feature: "CO",
    default_port: "Buenaventura",
  },
  ET: {
    code: "ET",
    name: "Ethiopia",
    currency: "ETB",
    currency_symbol: "Br",
    flag_emoji: "🇪🇹",
    data_source: { name: "ECX", url: "https://www.ecx.com.et/", kind: "api", reliability: 0.80, description: "Ethiopian Commodity Exchange" },
    harvest_calendar: { main_crop_start: 10, main_crop_end: 1, notes: "Harvest October–January" },
    ml_country_feature: "ET",
    default_port: "Djibouti",
  },
  BR: {
    code: "BR",
    name: "Brazil",
    currency: "BRL",
    currency_symbol: "R$",
    flag_emoji: "🇧🇷",
    data_source: { name: "CECAFÉ", url: "https://www.cecafe.com.br/", kind: "web", reliability: 0.82, description: "Conselho dos Exportadores de Café do Brasil" },
    harvest_calendar: { main_crop_start: 5, main_crop_end: 9, notes: "Main harvest May–September" },
    ml_country_feature: "BR",
    default_port: "Santos",
  },
};

export const SUPPORTED_COUNTRIES: SupportedCountry[] = ["PE", "CO", "ET", "BR"];

// Peru Regions
export interface PeruRegion {
  id: number;
  code: string;
  name: string;
  description_de: string | null;
  altitude_range: string | null;
  typical_varieties: string | null;
  typical_processing: string | null;
  logistics_notes: string | null;
  risk_notes: string | null;
}

// Cooperatives
export interface Cooperative {
  id: number;
  name: string;
  country: string;
  region: string | null;
  members_count: number | null;
  annual_production_kg: number | null;
  certifications: string[];
  contact_email: string | null;
  contact_phone: string | null;
  website_url: string | null;
  quality_score: number | null;
  reliability_score: number | null;
  economic_score: number | null;
  overall_score: number | null;
  next_action: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

// Roasters
export interface Roaster {
  id: number;
  company_name: string;
  city: string | null;
  state: string | null;
  country: string;
  roaster_type: string | null;
  annual_capacity_kg: number | null;
  certifications: string[];
  website_url: string | null;
  contact_email: string | null;
  contact_phone: string | null;
  sales_fit_score: number | null;
  overall_score: number | null;
  contact_status: string | null;
  last_contact_date: string | null;
  next_followup_date: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

// Shipments/Logistics
export interface Shipment {
  id: number;
  lot_id: number | null;
  cooperative_id: number | null;
  roaster_id: number | null;
  container_number: string;
  bill_of_lading: string;
  weight_kg: number;
  container_type: string;
  origin_port: string;
  destination_port: string;
  current_location: string | null;
  departure_date: string | null;
  estimated_arrival: string | null;
  actual_arrival: string | null;
  status: string;
  status_updated_at: string | null;
  delay_hours: number;
  notes: string | null;
  tracking_events: any[] | null;
  created_at: string;
  updated_at: string;
  // Legacy/alias fields for compatibility
  eta?: string | null;
  reference?: string;
  carrier?: string | null;
}

export interface ShipmentEvent {
  id: number;
  shipment_id: number;
  event_type: string;
  event_date: string;
  location: string | null;
  description: string | null;
  created_at: string;
}

// Deals/Margins
export interface Deal {
  id: number;
  reference: string;
  cooperative_id: number | null;
  roaster_id: number | null;
  lot_id: number | null;
  quantity_kg: number;
  purchase_price_per_kg: number;
  purchase_currency: string;
  sale_price_per_kg: number;
  sale_currency: string;
  freight_cost: number;
  insurance_cost: number;
  other_costs: number;
  margin_eur: number | null;
  margin_percentage: number | null;
  stage: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

// Deal/Lot creation and update types
export interface CreateDealRequest {
  origin_country: string;
  origin_region?: string;
  variety: string;
  process_method: string;
  quality_grade?: string;
  cupping_score?: number;
  weight_kg: number;
  price_per_kg?: number;
  currency?: string;
  certifications?: string[];
  harvest_date?: string;
  status?: string;
}

export interface UpdateDealRequest {
  origin_country?: string;
  origin_region?: string;
  variety?: string;
  process_method?: string;
  quality_grade?: string;
  cupping_score?: number;
  weight_kg?: number;
  price_per_kg?: number;
  currency?: string;
  certifications?: string[];
  harvest_date?: string;
  status?: string;
}

export interface MarginCalcRequest {
  purchase_price_per_kg: number;
  purchase_currency: string;
  landed_costs_per_kg: number;
  roast_and_pack_costs_per_kg: number;
  yield_factor: number;
  selling_price_per_kg: number;
  selling_currency: string;
  fx_usd_to_eur?: number | null;
}

export interface MarginCalcResult {
  computed_at: string;
  inputs: Record<string, any>;
  outputs: Record<string, any>;
}

// Margin Run type
export interface MarginRun {
  id: number;
  lot_id: number;
  profile: string;
  inputs: MarginCalcRequest;
  outputs: MarginCalcResult;
  created_at: string;
}

// ML Predictions
export interface FreightPredictionRequest {
  origin_port: string;
  destination_port: string;
  weight_kg: number;
  container_type: string;
  departure_date: string;
}

export interface FreightPredictionResponse {
  predicted_cost_usd: number;
  confidence_interval_low: number;
  confidence_interval_high: number;
  confidence_score: number;
  factors_considered: string[];
  similar_historical_shipments: number;
}

export interface PricePredictionRequest {
  origin_country: string;
  origin_region: string;
  variety: string;
  process: string;
  grade: string;
  cupping_score: number;
  certifications: string[];
  forecast_date: string;
}

export interface PricePredictionResponse {
  predicted_price_usd_per_kg: number;
  confidence_interval_low: number;
  confidence_interval_high: number;
  confidence_score: number;
  market_comparison: string;
  price_trend: string;
}

// ML Model types
export interface MLModel {
  id: number;
  model_type: string;
  name: string;
  version: string;
  accuracy?: number;
  created_at: string;
  last_trained?: string;
  status: string;
}

export interface FreightCostTrend {
  route: string;
  data_points: Array<{
    date: string;
    cost_usd: number;
  }>;
  trend: string;
  average_cost: number;
}

export interface PriceTrend {
  origin_region: string;
  data_points: Array<{
    date: string;
    price_usd_per_kg: number;
  }>;
  trend: string;
  forecast?: Array<{
    date: string;
    predicted_price: number;
  }>;
}

// News
export interface NewsItem {
  id: number;
  topic: string;
  title: string;
  source: string | null;
  url: string | null;
  published_at: string | null;
  created_at: string;
}

// Reports
export interface Report {
  id: number;
  name: string;
  kind: string;
  status: string;
  report_at: string;
  content: string | null;
}

// Market Data
export interface MarketPoint {
  value: number;
  unit?: string | null;
  currency?: string | null;
  observed_at: string;
}

export interface MarketSnapshot {
  [key: string]: MarketPoint | null;
}

// Pagination
export interface Paged<T> {
  items: T[];
  total: number;
  page?: number;
  limit?: number;
}

// Filters
export interface RegionFilters {
  min_production?: number;
  max_distance_to_callao?: number;
  min_cupping_score?: number;
}

export interface CooperativeFilters {
  country?: string;
  region?: string;
  min_capacity?: number;
  max_capacity?: number;
  certifications?: string[];
  min_score?: number;
  contact_status?: string;
}

export interface RoasterFilters {
  city?: string;
  country?: string;
  roaster_type?: string;
  min_capacity?: number;
  max_capacity?: number;
  certifications?: string[];
  min_sales_fit_score?: number;
  contact_status?: string;
}

export interface ShipmentFilters {
  status?: string;
  origin_port?: string;
  destination_port?: string;
  date_from?: string;
  date_to?: string;
}

export interface DealFilters {
  stage?: string;
  cooperative_id?: number;
  roaster_id?: number;
  min_margin?: number;
  date_from?: string;
  date_to?: string;
}

// Peru Region Intelligence types
export interface RegionElevationRange {
  min_m: number | null;
  max_m: number | null;
}

export interface RegionClimate {
  avg_temperature_c: number | null;
  rainfall_mm: number | null;
  humidity_pct: number | null;
}

export interface RegionProduction {
  volume_kg: number | null;
  share_pct: number | null;
  harvest_months: string | null;
}

export interface RegionQuality {
  typical_varieties: string | null;
  typical_processing: string | null;
  profile: string | null;
  consistency_score: number | null;
}

export interface RegionLogistics {
  main_port: string | null;
  transport_time_hours: number | null;
  cost_per_kg: number | null;
  infrastructure_score: number | null;
}

export interface RegionRisks {
  weather: string | null;
  political: string | null;
  logistics: string | null;
}

export interface RegionScores {
  growing_conditions: number;
  infrastructure: number;
  quality_consistency: number;
}

export interface RegionIntelligence {
  name: string;
  country: string;
  description: string | null;
  elevation_range: RegionElevationRange;
  climate: RegionClimate;
  soil_type: string | null;
  production: RegionProduction;
  quality: RegionQuality;
  logistics: RegionLogistics;
  risks: RegionRisks;
  scores: RegionScores;
}
