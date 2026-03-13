# Testing Strategy & Framework
## Enterprise-Grade Quality Assurance for CoffeeStudio

**Version:** 1.0.0  
**Document Type:** Technical Specification  
**Audience:** QA Engineers, DevOps, Backend Engineers

---

## Testing Pyramid

```
                    Manual Testing (Exploratory)
                  /                              \
                Smoke Tests (Deployment Checks)
              /                                    \
            Integration Tests (Multi-Component)
          /                                          \
        End-to-End Tests (Full Workflows)
      /                                                \
    API Tests (Endpoint Contracts)
  /                                                      \
Unit Tests (Individual Functions) ←← BASE (85%+ Coverage)
```

---

## 1. Unit Test Strategy (85%+ Coverage)

### Coverage Targets by Module

| Module | Target | Approach |
|--------|--------|----------|
| Providers | 90% | Mock HTTP responses |
| Services | 85% | Mock DB + external calls |
| Routes | 80% | Dependency injection |
| Models | 95% | Pydantic validation |
| Utils | 95% | Pure functions |

### Unit Test Examples

```python
# tests/unit/test_providers.py
import pytest
from app.providers.coffee_prices import CoffeePriceProvider
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_coffee_price_fetch_success():
    """Test successful price fetch"""
    provider = CoffeePriceProvider()
    
    with patch('yfinance.download') as mock_download:
        mock_download.return_value = {'Close': [2.15]}
        price = await provider.fetch_latest_price()
        
        assert price == 2.15
        mock_download.assert_called_once()

@pytest.mark.asyncio
async def test_coffee_price_fetch_fallback():
    """Test fallback on primary failure"""
    provider = CoffeePriceProvider()
    
    with patch('yfinance.download', side_effect=Exception("Network error")):
        with patch('stooq.download') as mock_fallback:
            mock_fallback.return_value = {'Close': [2.12]}
            price = await provider.fetch_latest_price()
            
            assert price == 2.12
            mock_fallback.assert_called_once()

@pytest.mark.asyncio
async def test_coffee_price_circuit_breaker():
    """Test circuit breaker after repeated failures"""
    provider = CoffeePriceProvider()
    
    # Fail 3 times to trigger breaker
    with patch('yfinance.download', side_effect=Exception("Network error")):
        for _ in range(3):
            try:
                await provider.fetch_latest_price()
            except:
                pass
    
    # Fourth attempt should fail immediately
    with pytest.raises(Exception, match="Circuit breaker"):
        await provider.fetch_latest_price()
```

### Test Organization

```
tests/
├── unit/
│   ├── test_providers.py
│   ├── test_services_ml.py
│   ├── test_services_pipeline.py
│   ├── test_models.py
│   └── test_utils.py
├── integration/
│   ├── test_end_to_end.py
│   ├── test_csv_import.py
│   └── test_api_contracts.py
├── performance/
│   ├── test_load.py
│   └── test_stress.py
├── security/
│   ├── test_sql_injection.py
│   ├── test_auth.py
│   └── test_rate_limiting.py
└── fixtures/
    ├── conftest.py
    ├── sample_data.py
    └── mock_apis.py
```

---

## 2. Integration Testing

### End-to-End Pipeline Test

```python
# tests/integration/test_end_to_end.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_full_data_pipeline():
    """Test complete data pipeline"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        
        # Step 1: Trigger collection
        response = await client.post("/api/data-pipeline/trigger-full-collection")
        assert response.status_code == 200
        collection_id = response.json()["collection_id"]
        
        # Step 2: Verify collection status
        for _ in range(10):  # Wait max 10 seconds
            response = await client.get(f"/api/data-pipeline/status/{collection_id}")
            assert response.status_code == 200
            
            if response.json()["status"] == "completed":
                break
            await asyncio.sleep(1)
        
        # Step 3: Generate features
        response = await client.post(
            "/api/feature-engineering/generate-features/1",
            json={"record_type": "price"}
        )
        assert response.status_code == 200
        features = response.json()
        assert len(features["features"]) >= 40
        
        # Step 4: Validate data quality
        response = await client.post(
            "/api/feature-engineering/validate-data-quality",
            json={"records": []}
        )
        assert response.status_code == 200
        assert response.json()["quality_score"] > 0.85
        
        # Step 5: Check monitoring
        response = await client.get("/api/monitoring/dashboard")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_csv_import_workflow():
    """Test complete CSV import"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        
        # Get template
        response = await client.get("/api/feature-engineering/import-template/price")
        assert response.status_code == 200
        template = response.json()
        
        # Create test CSV
        csv_data = generate_test_csv(template)
        
        # Upload
        response = await client.post(
            "/api/feature-engineering/import-bulk-csv",
            files={"file": ("test.csv", csv_data)},
            data={"data_type": "price"}
        )
        assert response.status_code == 200
        assert response.json()["imported_count"] > 0
        
        # Verify in database
        response = await client.get("/api/feature-engineering/get-imported")
        assert response.status_code == 200
        assert len(response.json()["records"]) > 0
```

### API Contract Testing

```python
# tests/integration/test_api_contracts.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_roasters_endpoint_contract():
    """Test roasters endpoint response contract"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/roasters?page=1&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        
        for item in data["items"]:
            assert "id" in item
            assert "name" in item
            assert "country" in item

@pytest.mark.asyncio
async def test_error_response_contract():
    """Test error response format"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/roasters/999999")
        assert response.status_code == 404
        
        error = response.json()
        assert "detail" in error
        assert "code" in error
        assert error["code"] == "NOT_FOUND"
```

---

## 3. Load & Performance Testing

### Locust Load Test

```python
# tests/performance/locust_test.py
from locust import HttpUser, task, between
import random

class CoffeeStudioLoadTest(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login before tests"""
        response = self.client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "test"}
        )
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(5)
    def get_market_data(self):
        """5x: Fetch market data (high frequency)"""
        self.client.get(
            "/api/data-pipeline/coffee-prices/latest",
            headers=self.headers
        )
    
    @task(3)
    def generate_features(self):
        """3x: Generate ML features"""
        self.client.post(
            "/api/feature-engineering/generate-features/1",
            json={"record_data": {"price": 2.10}},
            headers=self.headers
        )
    
    @task(2)
    def list_roasters(self):
        """2x: List roasters"""
        page = random.randint(1, 10)
        self.client.get(
            f"/roasters?page={page}&limit=25",
            headers=self.headers
        )
    
    @task(1)
    def check_health(self):
        """1x: Health check"""
        self.client.get("/api/monitoring/health")
```

**Run Load Test:**
```bash
# 1000 concurrent users, 50 spawn rate, 5 minute duration
locust -f tests/performance/locust_test.py \
  -u 1000 \
  -r 50 \
  --run-time 5m \
  -H http://localhost:8000 \
  --csv=results
```

**Expected Results:**
- Response time P95: <200ms
- Response time P99: <500ms
- Error rate: <0.5%
- Throughput: >10,000 req/min

---

## 4. Security Testing

### SQL Injection Tests

```python
# tests/security/test_sql_injection.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_sql_injection_protection():
    """Test SQL injection prevention"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        
        malicious_inputs = [
            "'; DROP TABLE market_observations; --",
            "1' OR '1'='1",
            "admin'--",
            "1; DELETE FROM roasters;",
        ]
        
        for payload in malicious_inputs:
            # Should not execute SQL
            response = await client.get(
                f"/roasters?search={payload}"
            )
            
            # Should return 400 or sanitized result
            assert response.status_code in [400, 200]
            
            # Verify tables still exist
            verify = await client.get("/roasters")
            assert verify.status_code == 200
```

### Authentication Tests

```python
# tests/security/test_auth.py
@pytest.mark.asyncio
async def test_missing_auth_token():
    """Test protection without auth token"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/protected-endpoint")
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_invalid_auth_token():
    """Test protection with invalid token"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/protected-endpoint",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_expired_auth_token():
    """Test protection with expired token"""
    expired_token = create_expired_token()
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/protected-endpoint",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401
```

### Rate Limiting Tests

```python
# tests/security/test_rate_limiting.py
@pytest.mark.asyncio
async def test_rate_limit_enforcement():
    """Test rate limit enforcement"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        
        # Make 101 requests (limit is 100/minute)
        for i in range(101):
            response = await client.get("/api/data-pipeline/health")
            
            if i < 100:
                assert response.status_code == 200
            else:
                assert response.status_code == 429  # Too Many Requests
```

---

## 5. Data Quality Testing

```python
# tests/integration/test_data_quality.py
import pytest
from app.services.ml.data_quality import DataQualityValidator

@pytest.mark.asyncio
async def test_price_anomaly_detection():
    """Test price spike detection"""
    validator = DataQualityValidator()
    
    # Normal prices
    normal = [2.00, 2.01, 1.99, 2.02]
    result = await validator.detect_anomalies(normal, type="price")
    assert len(result['anomalies']) == 0
    
    # With spike (150% increase)
    spike = [2.00, 2.01, 1.99, 5.00]
    result = await validator.detect_anomalies(spike, type="price")
    assert len(result['anomalies']) == 1
    assert result['anomalies'][0]['severity'] >= 4

@pytest.mark.asyncio
async def test_weather_extremes_detection():
    """Test weather anomaly detection"""
    validator = DataQualityValidator()
    
    # Impossible temps for Peru
    temps = [25.0, 25.5, 26.0, -50.0]
    result = await validator.detect_anomalies(temps, type="weather")
    assert len(result['anomalies']) > 0

@pytest.mark.asyncio
async def test_duplicate_detection():
    """Test duplicate record detection"""
    validator = DataQualityValidator()
    
    records = [
        {"id": 1, "price": 2.10, "date": "2024-01-01"},
        {"id": 2, "price": 2.10, "date": "2024-01-01"},
        {"id": 3, "price": 2.11, "date": "2024-01-01"},
    ]
    
    result = await validator.check_duplicates(records)
    # Exactly same records should be flagged
    assert len(result['duplicates']) >= 0
```

---

## 6. Test Execution Pipeline

### GitHub Actions CI/CD

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      
      - name: Run unit tests
        run: pytest tests/unit --cov=app --cov-report=xml
        env:
          DATABASE_URL: postgresql://postgres:test@localhost/test_db
      
      - name: Run integration tests
        run: pytest tests/integration
      
      - name: Run security tests
        run: pytest tests/security
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

---

## 7. Test Metrics & Thresholds

| Metric | Target | Threshold |
|--------|--------|-----------|
| Code Coverage | 85% | Fail if <80% |
| Unit Test Pass Rate | 100% | Fail if <95% |
| Integration Test Pass Rate | 100% | Fail if <90% |
| API Response Time P95 | <200ms | Fail if >500ms |
| Error Rate | <0.5% | Fail if >2% |
| Security Scan | 0 critical | Fail if critical |

---

## 8. Test Data Management

### Fixtures

```python
# tests/fixtures/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture
async def db_session():
    """Provide test database session"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()

@pytest.fixture
async def sample_price_data():
    """Sample price data"""
    return [
        {"origin": "Peru", "variety": "Arabica", "price": 2.10},
        {"origin": "Ethiopia", "variety": "Arabica", "price": 2.20},
        {"origin": "Colombia", "variety": "Arabica", "price": 2.15},
    ]

@pytest.fixture
async def sample_weather_data():
    """Sample weather data"""
    return [
        {
            "region": "Cajamarca",
            "temp_min": 15.0,
            "temp_max": 25.0,
            "precipitation": 120.5
        },
        # ... more regions
    ]
```

---

## 9. Deployment Validation Tests

```python
# tests/smoke/test_deployment.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_deployment_smoke():
    """Smoke test after deployment"""
    async with AsyncClient(app=app, base_url="http://localhost:8000") as client:
        
        # Health check
        response = await client.get("/api/monitoring/health")
        assert response.status_code == 200
        health = response.json()
        assert health["status"] == "healthy"
        
        # Database connectivity
        response = await client.get("/api/monitoring/health/database")
        assert response.status_code == 200
        
        # API responsiveness
        response = await client.get("/api/data-pipeline/sources")
        assert response.status_code == 200
        
        # Feature generation
        response = await client.post(
            "/api/feature-engineering/generate-features/1",
            json={}
        )
        assert response.status_code in [200, 404]  # 404 if not found
```

---

## 10. Continuous Integration Checklist

Before Merge to Main:
- [ ] Unit tests pass (85%+ coverage)
- [ ] Integration tests pass
- [ ] Security tests pass
- [ ] Code review approved
- [ ] No linting errors

Before Deployment:
- [ ] All CI checks pass
- [ ] Load tests pass (>10k req/min)
- [ ] Smoke tests pass
- [ ] Security audit pass
- [ ] Performance benchmarks pass

---

**Document Version:** 1.0.0  
**Last Updated:** March 14, 2026  
**Approved By:** QA Lead & DevOps Team
