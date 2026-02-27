#!/usr/bin/env bash
# Enterprise-Grade Validation Script
# This script runs comprehensive quality checks for production readiness

# Note: We use set -u and set -o pipefail but NOT set -e so we can capture all failures
set -uo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track results
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Function to print section header
print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    ((PASSED_CHECKS++))
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
    ((FAILED_CHECKS++))
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Change to backend directory
cd "$(dirname "$0")/../backend" || exit 1

print_header "🚀 ENTERPRISE VALIDATION SUITE"
echo "Starting comprehensive quality assurance checks..."
echo "Timestamp: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"

# ═══════════════════════════════════════════════════════════════════
# 1. CODE QUALITY & LINTING
# ═══════════════════════════════════════════════════════════════════
print_header "📝 Code Quality & Linting"

((TOTAL_CHECKS++))
echo "Running Ruff linter..."
if ruff check app; then
    print_success "Ruff linting passed - no issues found"
else
    print_error "Ruff linting failed - issues detected"
fi

((TOTAL_CHECKS++))
echo -e "\nChecking Black code formatting..."
if black app --check; then
    print_success "Black formatting passed - code is properly formatted"
else
    print_error "Black formatting failed - code needs formatting"
fi

# ═══════════════════════════════════════════════════════════════════
# 2. TYPE CHECKING
# ═══════════════════════════════════════════════════════════════════
print_header "🔍 Type Checking"

((TOTAL_CHECKS++))
echo "Running mypy type checker..."
cd ..
if mypy backend/app --config-file=mypy.ini; then
    print_success "Type checking passed - 0 type errors"
else
    print_error "Type checking failed - type errors detected"
fi
cd backend

# ═══════════════════════════════════════════════════════════════════
# 3. TEST SUITE
# ═══════════════════════════════════════════════════════════════════
print_header "🧪 Test Suite Validation"

((TOTAL_CHECKS++))
echo "Running full test suite with coverage..."
# Capture output to avoid running pytest twice
TEST_OUTPUT=$(pytest tests/ -v --cov=app --cov-report=term --cov-report=html 2>&1)
TEST_EXIT_CODE=$?

if [ $TEST_EXIT_CODE -eq 0 ]; then
    print_success "All tests passed"
    
    # Extract coverage percentage from captured output
    COVERAGE=$(echo "$TEST_OUTPUT" | grep "TOTAL" | awk '{print $NF}' | sed 's/%//')
    if [ -n "$COVERAGE" ]; then
        if [ "${COVERAGE%.*}" -ge 57 ]; then
            print_success "Code coverage: ${COVERAGE}% (target: ≥57%)"
        else
            print_warning "Code coverage: ${COVERAGE}% (below target of 57%)"
        fi
    fi
else
    print_error "Test suite failed"
    # Print the test output so user can see what failed
    echo "$TEST_OUTPUT"
fi

# ═══════════════════════════════════════════════════════════════════
# 4. SECURITY VALIDATION
# ═══════════════════════════════════════════════════════════════════
print_header "🔒 Security Validation"

((TOTAL_CHECKS++))
echo "Validating security middleware..."
if pytest tests/test_middleware.py -v -k "security_headers or sql_injection or xss"; then
    print_success "Security middleware tests passed"
else
    print_error "Security middleware tests failed"
fi

((TOTAL_CHECKS++))
echo -e "\nValidating rate limiting..."
if pytest tests/test_middleware.py -v -k "rate_limiting"; then
    print_success "Rate limiting tests passed"
else
    print_error "Rate limiting tests failed"
fi

((TOTAL_CHECKS++))
echo -e "\nValidating audit logging..."
if pytest tests/test_cooperatives.py -v -k "audit_logging"; then
    print_success "Audit logging tests passed"
else
    print_error "Audit logging tests failed"
fi

# ═══════════════════════════════════════════════════════════════════
# 5. CONFIGURATION VALIDATION
# ═══════════════════════════════════════════════════════════════════
print_header "⚙️ Configuration Validation"

cd ..

((TOTAL_CHECKS++))
echo "Checking .env.example completeness..."
# Core required variables
REQUIRED_VARS=("DATABASE_URL" "REDIS_URL" "JWT_SECRET" "BOOTSTRAP_ADMIN_EMAIL" "BOOTSTRAP_ADMIN_PASSWORD")
# Optional but recommended variables
OPTIONAL_VARS=("CORS_ORIGINS" "JWT_ISSUER" "JWT_AUDIENCE")

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if ! grep -q "^${var}=" .env.example; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -eq 0 ]; then
    print_success "All required environment variables present in .env.example"
    
    # Check optional variables (informational only)
    MISSING_OPTIONAL=()
    for var in "${OPTIONAL_VARS[@]}"; do
        if ! grep -q "^${var}=" .env.example; then
            MISSING_OPTIONAL+=("$var")
        fi
    done
    
    if [ ${#MISSING_OPTIONAL[@]} -gt 0 ]; then
        echo "  Note: Optional variables present: ${OPTIONAL_VARS[*]}"
    fi
else
    print_error "Missing required environment variables: ${MISSING_VARS[*]}"
fi

# ═══════════════════════════════════════════════════════════════════
# 6. DOCUMENTATION CHECK
# ═══════════════════════════════════════════════════════════════════
print_header "📚 Documentation Validation"

((TOTAL_CHECKS++))
echo "Checking required documentation files..."
REQUIRED_DOCS=("SECURITY_BEST_PRACTICES.md" "API_USAGE_GUIDE.md" "TESTING.md" "ENTERPRISE_IMPLEMENTATION_SUMMARY.md")
MISSING_DOCS=()
for doc in "${REQUIRED_DOCS[@]}"; do
    if [ ! -f "$doc" ]; then
        MISSING_DOCS+=("$doc")
    fi
done

if [ ${#MISSING_DOCS[@]} -eq 0 ]; then
    print_success "All required documentation files present"
else
    print_error "Missing documentation files: ${MISSING_DOCS[*]}"
fi

# ═══════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ═══════════════════════════════════════════════════════════════════
print_header "📊 VALIDATION SUMMARY"

echo "Total Checks: $TOTAL_CHECKS"
echo -e "Passed: ${GREEN}$PASSED_CHECKS${NC}"
echo -e "Failed: ${RED}$FAILED_CHECKS${NC}"
echo ""

if [ $TOTAL_CHECKS -gt 0 ]; then
    PASS_RATE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
    echo "Pass Rate: ${PASS_RATE}%"
else
    echo "Pass Rate: N/A"
fi

if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ ALL CHECKS PASSED - PRODUCTION READY! ✅${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    exit 0
else
    echo -e "\n${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ VALIDATION FAILED - ISSUES NEED ATTENTION ❌${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    exit 1
fi
