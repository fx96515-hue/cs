# Frontend Dashboards Documentation

## Overview

This implementation provides 5 comprehensive dashboards for the CoffeeStudio coffee trading platform, visualizing all backend data and enabling intuitive workflows for coffee trading operations between Peru and Germany.

## Architecture

- **Framework:** Next.js 14 with App Router
- **Language:** TypeScript (strict mode)
- **Data Fetching:** TanStack Query (React Query) for server state management
- **Charts:** Recharts for data visualization
- **Styling:** Custom CSS with dark theme optimized for coffee trading
- **Date Handling:** date-fns for date formatting and calculations

## Dashboard Pages

### 1. Peru Sourcing Intelligence Dashboard (`/peru-sourcing`)

**Purpose:** Discover and evaluate coffee cooperatives in Peru for sourcing opportunities.

**Features:**
- Peru coffee regions overview with region cards
- Filterable cooperatives directory
- Filters: Region, min capacity, min score, certifications
- Quality score indicators with color coding
- Direct links to cooperative detail pages

**API Endpoints Used:**
- `GET /regions/peru` - Peru coffee regions
- `GET /cooperatives` - Cooperatives with filtering

### 2. German Roasters Sales Dashboard (`/german-sales`)

**Purpose:** Manage relationships and sales pipeline with German specialty roasters.

**Features:**
- KPI cards: Total roasters, in pipeline, qualified, avg sales score
- Priority contacts list (top 10 by sales fit score)
- Pending followups widget with overdue highlighting
- Comprehensive roasters table with sorting
- Filters: City, roaster type, min sales score, contact status
- Date-aware followup tracking

**API Endpoints Used:**
- `GET /roasters` - Roasters with filtering

### 3. Shipments Tracking Dashboard (`/shipments`)

**Purpose:** Track coffee shipments from Peru to Germany/Europe.

**Features:**
- Active shipments cards with progress bars
- Arriving soon widget (shipments within 7 days)
- Visual status indicators and color coding
- Complete shipment history table
- Route information and carrier tracking
- ETA vs actual arrival tracking

**Note:** Currently uses mock data. Backend shipment API to be implemented.

### 4. Deals & Margin Calculator Dashboard (`/deals`)

**Purpose:** Manage coffee deals and calculate profitability margins.

**Features:**
- Deals overview KPIs
- Real-time margin calculator with live updates
- Interactive form inputs:
  - Purchase price per kg (USD)
  - Landed costs per kg (EUR)
  - Roast & pack costs per kg (EUR)
  - Yield factor (green to roasted)
  - Selling price per kg (EUR)
- Cost breakdown pie chart
- Margin calculation results with detailed breakdown
- Active lots/deals table

**API Endpoints Used:**
- `GET /lots` - Lots/deals listing
- `POST /margins/calc` - Margin calculation

### 5. Analytics & ML Predictions Dashboard (`/analytics`)

**Purpose:** Use machine learning models to predict costs and prices.

**Features:**
- **Freight Cost Predictor:**
  - Origin/destination port selection
  - Weight and container type
  - Departure date
  - Prediction with confidence intervals
  - Historical comparison
  
- **Coffee Price Predictor:**
  - Origin, variety, process method
  - Quality grade and cupping score
  - Certifications
  - Price prediction with market comparison
  
- Business Intelligence Cards:
  - Active cooperatives count
  - German roasters count
  - Average quality score
  - Average sales score

**API Endpoints Used:**
- `POST /ml/predict-freight` - Freight cost prediction
- `POST /ml/predict-coffee-price` - Coffee price prediction
- `GET /ml/freight-cost-trend` - Historical freight trends
- `GET /ml/models` - ML models listing

## Shared Components

### Chart Components (`app/charts/`)

- **LineChart.tsx** - Time series visualization
- **BarChart.tsx** - Comparison charts
- **PieChart.tsx** - Distribution/breakdown charts

All charts use Recharts with consistent dark theme styling.

### React Query Hooks (`app/hooks/`)

- **usePeruRegions.ts** - Peru regions and cooperatives data
- **useRoasters.ts** - German roasters data
- **useDeals.ts** - Deals and margin calculations
- **usePredictions.ts** - ML predictions

All hooks include:
- Loading states
- Error handling
- Automatic cache invalidation
- TypeScript type safety

### Type Definitions (`app/types/index.ts`)

Complete TypeScript interfaces matching backend Pydantic schemas for:
- Regions, Cooperatives, Roasters
- Shipments, Deals, Margins
- ML Predictions
- News, Reports, Market Data

## Styling

Custom CSS with coffee trading optimized dark theme:
- Dark blue/navy background
- Subtle borders and shadows
- Color-coded status indicators (green/yellow/red)
- Responsive grid layouts
- Hover states and interactive feedback

## Navigation

Updated sidebar includes:
- Dashboard (main overview)
- Peru Sourcing
- German Sales
- Shipments
- Deals & Margins
- Analytics & ML
- Cooperatives (legacy)
- Röstereien (legacy)
- Marktradar (news)
- Reports
- Operations

## Development

### Build
```bash
cd apps/web
npm install
npm run build
```

### Development Server
```bash
npm run dev
```

### Lint
```bash
npm run lint
```

## Environment Variables

Set in `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Falls back to:
- `http://api.localhost` (Traefik routing)
- `http://localhost:8000` (direct backend)

## Future Enhancements

### Planned Features
- Interactive maps with react-leaflet for Peru regions and shipment routes
- TanStack Table for advanced sorting/filtering
- Funnel chart for sales pipeline visualization
- Gauge charts for score indicators
- WebSocket integration for real-time updates
- Advanced filtering with saved views
- Export functionality (CSV, PDF reports)
- Collaborative features (comments, task assignments)

### Technical Improvements
- Component testing with Vitest
- Storybook for component documentation
- Dark mode toggle
- Internationalization (i18n)
- Performance optimizations with lazy loading

## Integration Testing

To test with live backend:

1. Start backend: `docker compose up backend`
2. Run migrations: `docker compose exec backend alembic upgrade head`
3. Bootstrap admin user: `curl -X POST http://localhost:8000/auth/dev/bootstrap`
4. Start frontend: `cd apps/web && npm run dev`
5. Login with: admin@coffeestudio.com / adminadmin
6. Navigate to dashboards

## API Documentation

Backend API docs available at: http://localhost:8000/docs

All dashboard API calls require authentication via JWT token (stored in localStorage as 'token').

## Troubleshooting

### CORS Issues
If API calls fail with CORS errors, verify backend CORS settings allow `http://localhost:3000`.

### Authentication Errors
Clear localStorage and login again if getting 401/403 errors:
```javascript
localStorage.clear();
```

### Type Errors
Ensure TypeScript types in `app/types/index.ts` match backend schemas. Check backend schemas at `apps/api/app/schemas/`.

## Support

For issues or questions:
1. Check backend API documentation
2. Verify API endpoints match backend routes
3. Review browser console for errors
4. Check network tab for failed requests
