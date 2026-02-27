# Integration Testing Quick Reference

## Running the Integration Smoke Test

After starting the platform with `docker compose up`, run the comprehensive smoke test:

```bash
bash scripts/integration_smoke_test.sh
```

### What It Tests

The smoke test validates ALL critical integrations:

1. **Service Health Checks**
   - Backend API health
   - Database connectivity
   - Redis connectivity
   - Frontend accessibility

2. **Authentication & Bootstrap**
   - Admin user bootstrap
   - Login with correct credentials
   - JWT token acquisition
   - Auth endpoint (`/auth/me`)

3. **Core API Endpoints**
   - Health endpoint (`/health`)
   - Metrics endpoint (`/metrics`)

4. **Data Management APIs**
   - Cooperatives (create, list, get)
   - Roasters (create, list)
   - Lots/Deals (create, list)
   - Margins calculation
   - Peru regions (list, seed)
   - Peru sourcing
   - Shipments (create, list, get active)

5. **Advanced Features**
   - ML predictions (freight cost)
   - News API
   - Reports API
   - Market data API

6. **Cleanup**
   - Deletes all test data created during the test run

### Output

The script provides colored output:
- 🟢 **GREEN [PASS]**: Test passed
- 🔴 **RED [FAIL]**: Test failed
- 🟡 **YELLOW [SKIP]**: Test skipped (optional feature not available)
- 🔵 **BLUE [INFO]**: Informational message

### Exit Codes

- **0**: All tests passed ✅
- **1**: One or more tests failed ❌

### Example Run

```bash
$ bash scripts/integration_smoke_test.sh

========================================
1. Service Health Checks
========================================
[INFO] Waiting for Backend API to be ready...
[PASS] Backend API is ready
[PASS] Database connectivity verified
[PASS] Frontend is accessible at http://localhost:3000

========================================
2. Database Migrations
========================================
[INFO] Running Alembic migrations...
[PASS] Database migrations completed

... (more tests) ...

========================================
15. Summary
========================================
================================================
Passed: 42
Failed: 0
Skipped: 3
Total: 45
================================================

✓ All tests passed!
```

## Running E2E Integration Tests

The E2E tests are part of the pytest suite:

```bash
cd apps/api
pytest tests/integration/test_e2e_flows.py -v
```

These tests verify:
- Cooperative creation → sourcing analysis flow
- Roaster creation → sales fit scoring flow
- Lot creation → margin calculation flow
- Shipments CRUD operations
- ML prediction endpoints
- Frontend accessibility
- Health and metrics endpoints

## Environment Variables

Both test suites respect these environment variables:

```bash
# Backend URL (default: http://localhost:8000)
export BASE_URL="http://localhost:8000"

# Frontend URL (default: http://localhost:3000)
export FRONTEND_URL="http://localhost:3000"

# Bootstrap credentials (default: admin@coffeestudio.com / adminadmin)
export BOOTSTRAP_ADMIN_EMAIL="admin@coffeestudio.com"
export BOOTSTRAP_ADMIN_PASSWORD="adminadmin"
```

## Troubleshooting

### Services Not Ready
If the smoke test fails because services aren't ready:
1. Check Docker containers are running: `docker compose ps`
2. Check backend logs: `docker compose logs backend`
3. Wait longer for services to start (increase MAX_RETRIES in script)

### Authentication Failed
If authentication fails:
1. Verify `.env` file has correct credentials
2. Check BOOTSTRAP_ADMIN_PASSWORD matches what you use
3. Manually bootstrap: `curl -X POST http://localhost:8000/auth/dev/bootstrap`

### Tests Fail on ML Endpoints
ML endpoints may return 503 if models aren't trained yet. This is expected and tests will skip these.

### Frontend Not Accessible
If frontend test fails:
1. Check frontend is running: `docker compose ps frontend`
2. Check frontend logs: `docker compose logs frontend`
3. Verify port 3000 is not blocked

## Integration with CI/CD

Add to your CI pipeline:

```yaml
- name: Run Integration Smoke Tests
  run: |
    docker compose up -d
    sleep 30  # Wait for services
    bash scripts/integration_smoke_test.sh
  
- name: Run E2E Tests
  run: |
    cd apps/api
    pytest tests/integration/test_e2e_flows.py -v
```

## Coverage

The integration tests cover:
- ✅ All CRUD operations for main entities
- ✅ Authentication and authorization
- ✅ Database migrations
- ✅ API endpoint correctness
- ✅ Error handling
- ✅ Service connectivity
- ✅ Frontend accessibility
- ✅ ML predictions (when available)
- ✅ Data cleanup

Total API endpoints tested: **25+**
