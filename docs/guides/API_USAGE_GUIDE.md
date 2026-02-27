# API Usage Guide

Complete guide to using the CoffeeStudio Platform API with examples.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [Cooperatives](#cooperatives)
4. [Roasters](#roasters)
5. [Lots](#lots)
6. [Shipments](#shipments)
7. [Margin Calculations](#margin-calculations)
8. [Reports](#reports)
9. [ML Predictions](#ml-predictions)
10. [Error Handling](#error-handling)

---

## Getting Started

### Base URL

```
Development: http://localhost:8000
Production: https://api.coffeestudio.com
```

### API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Response Format

All successful responses return JSON:
```json
{
  "id": 1,
  "name": "Resource Name",
  "created_at": "2025-12-29T10:00:00Z"
}
```

Error responses follow this format:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {}
  }
}
```

---

## Authentication

### Bootstrap Admin User (Development Only)

Create the first admin user:

```bash
curl -X POST http://localhost:8000/auth/dev/bootstrap \
  -H "Content-Type: application/json"
```

Response:
```json
{
  "message": "Admin user created",
  "email": "admin@coffeestudio.com",
  "note": "Password: adminadmin (CHANGE IMMEDIATELY)"
}
```

### Login

Obtain a JWT token:

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@coffeestudio.com",
    "password": "adminadmin"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "admin@coffeestudio.com",
    "role": "admin",
    "is_active": true
  }
}
```

### Using the Token

Include the token in the Authorization header:

```bash
curl -X GET http://localhost:8000/cooperatives \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Get Current User

```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

---

## Cooperatives

### List Cooperatives

```bash
curl -X GET http://localhost:8000/cooperatives \
  -H "Authorization: Bearer <TOKEN>"
```

Query parameters:
- `skip`: Offset (default: 0)
- `limit`: Number of results (default: 100)

Response:
```json
[
  {
    "id": 1,
    "name": "Cooperativa Cafetalera La Florida",
    "region": "Cajamarca",
    "altitude_min": 1200,
    "altitude_max": 1800,
    "hectares": 500,
    "farmer_count": 150,
    "contact_email": "info@laflorida.pe",
    "certifications": ["Organic", "Fair Trade"],
    "created_at": "2025-12-29T10:00:00Z",
    "updated_at": "2025-12-29T10:00:00Z"
  }
]
```

### Get Single Cooperative

```bash
curl -X GET http://localhost:8000/cooperatives/1 \
  -H "Authorization: Bearer <TOKEN>"
```

### Create Cooperative

**Required Role:** admin, analyst

```bash
curl -X POST http://localhost:8000/cooperatives \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cooperativa Valle del Café",
    "region": "Cusco",
    "altitude_min": 1400,
    "altitude_max": 2000,
    "hectares": 300,
    "farmer_count": 80,
    "contact_email": "contact@valledecafe.pe",
    "contact_phone": "+51-1-234-5678",
    "website": "https://valledecafe.pe",
    "certifications": ["Organic", "Rainforest Alliance"],
    "varietals": ["Caturra", "Typica", "Bourbon"],
    "processing_methods": ["Washed", "Honey"],
    "harvest_months": ["May", "June", "July", "August"]
  }'
```

### Update Cooperative

**Required Role:** admin, analyst

```bash
curl -X PUT http://localhost:8000/cooperatives/1 \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cooperativa Valle del Café (Updated)",
    "hectares": 350
  }'
```

### Delete Cooperative

**Required Role:** admin

```bash
curl -X DELETE http://localhost:8000/cooperatives/1 \
  -H "Authorization: Bearer <TOKEN>"
```

---

## Roasters

### List Roasters

```bash
curl -X GET http://localhost:8000/roasters \
  -H "Authorization: Bearer <TOKEN>"
```

Response:
```json
[
  {
    "id": 1,
    "name": "Rösterei München",
    "city": "München",
    "country": "Germany",
    "contact_email": "info@roesterei-muenchen.de",
    "website": "https://roesterei-muenchen.de",
    "annual_volume_kg": 50000,
    "specialty_focus": true,
    "created_at": "2025-12-29T10:00:00Z"
  }
]
```

### Create Roaster

**Required Role:** admin, analyst

```bash
curl -X POST http://localhost:8000/roasters \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Berlin Coffee Roasters",
    "city": "Berlin",
    "country": "Germany",
    "contact_email": "hello@berlinroasters.de",
    "contact_phone": "+49-30-1234567",
    "website": "https://berlinroasters.de",
    "annual_volume_kg": 30000,
    "specialty_focus": true,
    "preferred_origins": ["Peru", "Ethiopia", "Colombia"],
    "preferred_profiles": ["Light", "Medium"]
  }'
```

---

## Lots

### List Lots

```bash
curl -X GET http://localhost:8000/lots \
  -H "Authorization: Bearer <TOKEN>"
```

Response:
```json
[
  {
    "id": 1,
    "lot_number": "LOT-2025-001",
    "cooperative_id": 1,
    "weight_kg": 10000,
    "grade": "AA",
    "cup_score": 86.5,
    "price_per_kg_usd": 4.50,
    "harvest_date": "2025-08-15",
    "status": "available",
    "created_at": "2025-12-29T10:00:00Z"
  }
]
```

### Create Lot

```bash
curl -X POST http://localhost:8000/lots \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "lot_number": "LOT-2025-002",
    "cooperative_id": 1,
    "weight_kg": 5000,
    "grade": "A",
    "cup_score": 85.0,
    "price_per_kg_usd": 4.20,
    "harvest_date": "2025-08-20",
    "varietals": ["Caturra", "Bourbon"],
    "processing_method": "Washed",
    "altitude_masl": 1600,
    "notes": "Bright acidity, notes of citrus and chocolate"
  }'
```

---

## Shipments

### List All Shipments

Get all shipments with optional filters:

```bash
curl -X GET "http://localhost:8000/shipments/?status=in_transit" \
  -H "Authorization: Bearer <TOKEN>"
```

Query parameters:
- `status`: Filter by status (in_transit, delivered, customs, delayed, planned)
- `origin_port`: Filter by origin port
- `destination_port`: Filter by destination port
- `limit`: Maximum results (default: 200, max: 1000)

Response:
```json
[
  {
    "id": 1,
    "lot_id": 5,
    "cooperative_id": 2,
    "roaster_id": 3,
    "container_number": "MSCU1234567",
    "bill_of_lading": "BOL-2024-001",
    "weight_kg": 18000.0,
    "container_type": "40ft",
    "origin_port": "Callao, Peru",
    "destination_port": "Hamburg, Germany",
    "current_location": "Panama Canal",
    "departure_date": "2024-01-15",
    "estimated_arrival": "2024-02-20",
    "actual_arrival": null,
    "status": "in_transit",
    "status_updated_at": "2024-01-15T10:00:00Z",
    "delay_hours": 0,
    "tracking_events": [
      {
        "timestamp": "2024-01-15T08:00:00Z",
        "location": "Callao Port",
        "event": "Departure",
        "details": "Container loaded and departed"
      },
      {
        "timestamp": "2024-01-20T14:00:00Z",
        "location": "Panama Canal",
        "event": "Transit",
        "details": "Passed through Panama Canal"
      }
    ],
    "notes": "High priority shipment"
  }
]
```

### Get Active Shipments

Get all shipments currently in transit:

```bash
curl -X GET http://localhost:8000/shipments/active \
  -H "Authorization: Bearer <TOKEN>"
```

### Get Delayed Shipments

Get all shipments with delays:

```bash
curl -X GET http://localhost:8000/shipments/delayed \
  -H "Authorization: Bearer <TOKEN>"
```

### Create Shipment

```bash
curl -X POST http://localhost:8000/shipments/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "lot_id": 5,
    "cooperative_id": 2,
    "roaster_id": 3,
    "container_number": "MSCU1234567",
    "bill_of_lading": "BOL-2024-001",
    "weight_kg": 18000.0,
    "container_type": "40ft",
    "origin_port": "Callao, Peru",
    "destination_port": "Hamburg, Germany",
    "departure_date": "2024-01-15",
    "estimated_arrival": "2024-02-20",
    "notes": "High priority shipment"
  }'
```

**Container Types:**
- `20ft`: 20-foot container
- `40ft`: 40-foot container
- `40ft_hc`: 40-foot high cube container

Response: Returns the created shipment object.

### Get Shipment by ID

```bash
curl -X GET http://localhost:8000/shipments/1 \
  -H "Authorization: Bearer <TOKEN>"
```

### Update Shipment

```bash
curl -X PATCH http://localhost:8000/shipments/1 \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "current_location": "Atlantic Ocean",
    "status": "in_transit",
    "delay_hours": 24
  }'
```

**Valid Status Values:**
- `planned`: Shipment is planned
- `in_transit`: Currently shipping
- `customs`: In customs clearance
- `delivered`: Successfully delivered
- `delayed`: Delayed shipment

### Add Tracking Event

Add a location update to a shipment:

```bash
curl -X POST http://localhost:8000/shipments/1/track \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-01-25T10:00:00Z",
    "location": "Atlantic Ocean",
    "event": "In Transit",
    "details": "Halfway to destination"
  }'
```

Response: Returns the updated shipment with all tracking events.

### Delete Shipment

```bash
curl -X DELETE http://localhost:8000/shipments/1 \
  -H "Authorization: Bearer <TOKEN>"
```

Response:
```json
{
  "status": "deleted"
}
```

---

## Margin Calculations

### Calculate Margin

Calculate profit margins for a lot:

```bash
curl -X POST http://localhost:8000/lots/1/margins/calculate \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "selling_price_eur_per_kg": 12.50,
    "freight_cost_usd": 2500,
    "insurance_cost_usd": 300,
    "customs_duties_eur": 500,
    "other_costs_eur": 200
  }'
```

Response:
```json
{
  "lot_id": 1,
  "total_cost_eur": 48500.00,
  "total_revenue_eur": 125000.00,
  "gross_margin_eur": 76500.00,
  "margin_percentage": 61.2,
  "cost_breakdown": {
    "coffee_cost_eur": 45000.00,
    "freight_eur": 2300.00,
    "insurance_eur": 276.00,
    "customs_eur": 500.00,
    "other_eur": 200.00
  }
}
```

### Save Margin Run

Save a margin calculation:

```bash
curl -X POST http://localhost:8000/lots/1/margins \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "selling_price_eur_per_kg": 12.50,
    "freight_cost_usd": 2500,
    "insurance_cost_usd": 300,
    "customs_duties_eur": 500,
    "other_costs_eur": 200,
    "notes": "Q1 2025 pricing scenario"
  }'
```

### List Margin Runs

Get all saved margin calculations for a lot:

```bash
curl -X GET http://localhost:8000/lots/1/margins \
  -H "Authorization: Bearer <TOKEN>"
```

---

## Reports

### List Reports

```bash
curl -X GET http://localhost:8000/reports \
  -H "Authorization: Bearer <TOKEN>"
```

### Get Report

```bash
curl -X GET http://localhost:8000/reports/1 \
  -H "Authorization: Bearer <TOKEN>"
```

Response:
```json
{
  "id": 1,
  "report_date": "2025-12-29",
  "title": "Daily Market Report - December 29, 2025",
  "content": "# Market Overview\n\n...",
  "created_at": "2025-12-29T08:00:00Z"
}
```

### Generate Report

Trigger report generation (async via Celery):

```bash
curl -X POST http://localhost:8000/reports/generate \
  -H "Authorization: Bearer <TOKEN>"
```

---

## ML Predictions

### Predict Freight Cost

```bash
curl -X POST http://localhost:8000/ml/predict-freight \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "origin_port": "Callao",
    "destination_port": "Hamburg",
    "weight_kg": 10000,
    "container_type": "20ft"
  }'
```

Response:
```json
{
  "predicted_cost_usd": 2850.50,
  "confidence_lower": 2650.00,
  "confidence_upper": 3100.00,
  "confidence_score": 0.85,
  "model_version": "v1.0"
}
```

### Predict Coffee Price

```bash
curl -X POST http://localhost:8000/ml/predict-coffee-price \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "origin_country": "Peru",
    "quality_grade": "AA",
    "cup_score": 86.5,
    "month": 3
  }'
```

Response:
```json
{
  "predicted_price_usd_per_kg": 4.85,
  "confidence_lower": 4.50,
  "confidence_upper": 5.20,
  "confidence_score": 0.82,
  "trend": "increasing"
}
```

### Get Freight Cost Trend

```bash
curl -X GET "http://localhost:8000/ml/freight-cost-trend?route=Callao-Hamburg&months=12" \
  -H "Authorization: Bearer <TOKEN>"
```

Response:
```json
{
  "route": "Callao-Hamburg",
  "data_points": 52,
  "trend": [
    {"date": "2024-12-29", "cost_usd": 2700},
    {"date": "2025-01-05", "cost_usd": 2750},
    ...
  ],
  "average_cost": 2825.50,
  "trend_direction": "stable"
}
```

---

## Error Handling

### Common Errors

#### 400 Bad Request
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "loc": ["body", "email"],
        "msg": "invalid email format",
        "type": "value_error.email"
      }
    ]
  }
}
```

#### 401 Unauthorized
```json
{
  "error": {
    "code": "HTTP_ERROR",
    "message": "Invalid credentials"
  }
}
```

#### 403 Forbidden
```json
{
  "error": {
    "code": "HTTP_ERROR",
    "message": "Insufficient permissions"
  }
}
```

#### 404 Not Found
```json
{
  "error": {
    "code": "HTTP_ERROR",
    "message": "Resource not found"
  }
}
```

#### 409 Conflict
```json
{
  "error": {
    "code": "DATABASE_INTEGRITY_ERROR",
    "message": "A record with this value already exists"
  }
}
```

#### 422 Unprocessable Entity
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [...]
  }
}
```

#### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded"
}
```

#### 500 Internal Server Error
```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred. Please try again later."
  }
}
```

---

## Rate Limits

Default rate limits:
- **Global:** 200 requests per minute per IP
- **Login:** 5 requests per minute per IP

Headers returned with rate limit info:
```
X-RateLimit-Limit: 200
X-RateLimit-Remaining: 195
X-RateLimit-Reset: 1704067200
```

---

## Pagination

List endpoints support pagination:

```bash
curl -X GET "http://localhost:8000/cooperatives?skip=0&limit=10" \
  -H "Authorization: Bearer <TOKEN>"
```

Parameters:
- `skip`: Number of records to skip (default: 0)
- `limit`: Number of records to return (default: 100, max: 100)

---

## Best Practices

1. **Always use HTTPS** in production
2. **Store tokens securely** - Use httpOnly cookies or secure storage
3. **Handle rate limits** - Implement exponential backoff
4. **Validate responses** - Check status codes and handle errors
5. **Use pagination** - Don't request all records at once
6. **Cache responses** - Reduce API calls where appropriate
7. **Include User-Agent** - Help us improve the API

Example with User-Agent:
```bash
curl -X GET http://localhost:8000/cooperatives \
  -H "Authorization: Bearer <TOKEN>" \
  -H "User-Agent: MyApp/1.0"
```

---

## SDKs & Libraries

### Python

```python
import requests

class CoffeeStudioClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def get_cooperatives(self):
        response = requests.get(
            f"{self.base_url}/cooperatives",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage
client = CoffeeStudioClient("http://localhost:8000", "your-token")
cooperatives = client.get_cooperatives()
```

### JavaScript/TypeScript

```typescript
class CoffeeStudioClient {
  constructor(private baseUrl: string, private token: string) {}

  async getCooperatives() {
    const response = await fetch(`${this.baseUrl}/cooperatives`, {
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    return response.json();
  }
}

// Usage
const client = new CoffeeStudioClient('http://localhost:8000', 'your-token');
const cooperatives = await client.getCooperatives();
```

---

## Support

For API questions or issues:
- **Email:** api-support@coffeestudio.com
- **Documentation:** https://docs.coffeestudio.com
- **GitHub Issues:** https://github.com/fx96515-hue/coffeestudio-platform/issues

---

**Last Updated:** 2025-12-29  
**API Version:** 0.4.0  
**Maintainer:** CoffeeStudio Dev Team
