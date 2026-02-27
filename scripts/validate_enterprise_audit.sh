#!/usr/bin/env bash
# Quick validation script for Enterprise Audit System
# This script performs basic checks to ensure the audit system is properly integrated

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================"
echo "Enterprise Audit System Validation"
echo "========================================"
echo ""

# Change to repository root
cd "$(dirname "$0")/.."

echo "1. Checking file structure..."

# Check that all key files exist
FILES=(
    "apps/api/app/core/audit.py"
    "apps/api/app/middleware/__init__.py"
    "apps/api/app/middleware/security_headers.py"
    "apps/api/app/middleware/input_validation.py"
    "apps/api/app/core/error_handlers.py"
    "apps/api/app/core/export.py"
    "apps/api/tests/test_audit_logging.py"
)

ALL_FILES_EXIST=true
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file (MISSING)"
        ALL_FILES_EXIST=false
    fi
done

echo ""
echo "2. Checking Python syntax..."

# Check Python syntax for key files
cd apps/api
SYNTAX_OK=true
for file in app/core/audit.py app/middleware/input_validation.py app/middleware/security_headers.py app/core/error_handlers.py app/core/export.py app/main.py; do
    if python -m py_compile "$file" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file (SYNTAX ERROR)"
        SYNTAX_OK=false
    fi
done

echo ""
echo "3. Checking imports and integration..."

# Check that main.py imports middleware correctly
if grep -q "from app.middleware import InputValidationMiddleware, SecurityHeadersMiddleware" app/main.py; then
    echo -e "${GREEN}✓${NC} Middleware imported in main.py"
else
    echo -e "${RED}✗${NC} Middleware import missing in main.py"
fi

# Check that main.py imports error handlers
if grep -q "from app.core.error_handlers import" app/main.py; then
    echo -e "${GREEN}✓${NC} Error handlers imported in main.py"
else
    echo -e "${RED}✗${NC} Error handlers import missing in main.py"
fi

# Check that routes import AuditLogger
# We expect audit logging in key routes: auth, cooperatives, roasters, lots, market, shipments, sources
EXPECTED_MIN_ROUTES=5
ROUTES_WITH_AUDIT=$(grep -l "from app.core.audit import AuditLogger" app/api/routes/*.py | wc -l)
if [ "$ROUTES_WITH_AUDIT" -ge "$EXPECTED_MIN_ROUTES" ]; then
    echo -e "${GREEN}✓${NC} AuditLogger used in $ROUTES_WITH_AUDIT route files"
else
    echo -e "${YELLOW}⚠${NC} AuditLogger used in only $ROUTES_WITH_AUDIT route files (expected $EXPECTED_MIN_ROUTES+)"
fi

echo ""
echo "4. Checking test files..."

TEST_FILES=(
    "tests/test_audit_logging.py"
    "tests/test_middleware.py"
    "tests/test_export.py"
)

for test_file in "${TEST_FILES[@]}"; do
    if [ -f "$test_file" ]; then
        # Count test functions in file
        TEST_COUNT=$(grep -c "^def test_" "$test_file" 2>/dev/null || echo "0")
        echo -e "${GREEN}✓${NC} $test_file ($TEST_COUNT tests)"
    else
        echo -e "${RED}✗${NC} $test_file (MISSING)"
    fi
done

echo ""
echo "5. Checking Docker configuration..."

cd ..
if [ -f "docker-compose.yml" ]; then
    echo -e "${GREEN}✓${NC} docker-compose.yml exists"
    
    # Check if backend service is defined
    if grep -q "backend:" docker-compose.yml; then
        echo -e "${GREEN}✓${NC} Backend service defined"
    else
        echo -e "${RED}✗${NC} Backend service not defined"
    fi
    
    # Check if Dockerfile exists
    if [ -f "apps/api/Dockerfile" ]; then
        echo -e "${GREEN}✓${NC} apps/api/Dockerfile exists"
    else
        echo -e "${RED}✗${NC} apps/api/Dockerfile missing"
    fi
else
    echo -e "${RED}✗${NC} docker-compose.yml missing"
fi

echo ""
echo "6. Checking documentation..."

DOC_FILES=(
    "docs/security/SECURITY_BEST_PRACTICES.md"
    "docs/guides/API_USAGE_GUIDE.md"
    "docs/architecture/ENTERPRISE_IMPLEMENTATION_SUMMARY.md"
    "ENTERPRISE_AUDIT_PR_SUMMARY.md"
)

for doc in "${DOC_FILES[@]}"; do
    if [ -f "$doc" ]; then
        echo -e "${GREEN}✓${NC} $doc"
    else
        echo -e "${YELLOW}⚠${NC} $doc (optional)"
    fi
done

echo ""
echo "========================================"
echo "Validation Summary"
echo "========================================"

if [ "$ALL_FILES_EXIST" = true ] && [ "$SYNTAX_OK" = true ]; then
    echo -e "${GREEN}✅ Enterprise Audit System appears to be correctly implemented!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Set up environment variables in .env"
    echo "  2. Run: docker compose up --build"
    echo "  3. Run tests: cd apps/api && pytest tests/ -v"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Some issues were found. Please review the output above.${NC}"
    echo ""
    exit 1
fi
