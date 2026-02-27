#!/bin/bash
set -euo pipefail

echo "🔍 Docker Stack Validation Script"
echo "=================================="

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_passed=0
check_failed=0

pass() {
    echo -e "${GREEN}✓${NC} $1"
    check_passed=$((check_passed + 1))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    check_failed=$((check_failed + 1))
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# 1. Check Docker Compose files syntax
echo -e "\n📋 Checking Docker Compose configuration..."
if docker compose -f docker-compose.yml config > /dev/null 2>&1; then
    pass "docker-compose.yml is valid"
else
    fail "docker-compose.yml has syntax errors"
fi

if [ -f "docker-compose.stack.yml" ]; then
    if docker compose -f docker-compose.stack.yml config > /dev/null 2>&1; then
        pass "docker-compose.stack.yml is valid"
    else
        fail "docker-compose.stack.yml has syntax errors"
    fi
fi

# 2. Check required environment files
echo -e "\n🔐 Checking environment configuration..."
if [ -f ".env" ]; then
    pass ".env file exists"
    
    # Check critical variables
    required_vars=("DATABASE_URL" "REDIS_URL" "JWT_SECRET")
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" .env; then
            pass "$var is defined in .env"
        else
            fail "$var is missing from .env"
        fi
    done
else
    fail ".env file is missing"
fi

# 3. Check Docker networks
echo -e "\n🌐 Verifying Docker network configuration..."
if docker compose -f docker-compose.yml config | grep -q "networks:"; then
    pass "Docker networks configured"
else
    warn "No custom Docker networks defined"
fi

# 4. Check service health checks
echo -e "\n❤️ Verifying service health checks..."
services=("backend" "frontend" "postgres" "redis")
for service in "${services[@]}"; do
    if docker compose -f docker-compose.yml config | grep -A 10 "^  $service:" | grep -q "healthcheck:"; then
        pass "$service has healthcheck configured"
    else
        warn "$service missing healthcheck definition"
    fi
done

# 5. Check volume persistence
echo -e "\n💾 Checking data persistence configuration..."
if docker compose -f docker-compose.yml config | grep -q "volumes:"; then
    pass "Named volumes configured for persistence"
else
    fail "No persistent volumes configured"
fi

# 6. Validate service dependencies
echo -e "\n🔗 Checking service dependencies..."
if docker compose -f docker-compose.yml config | grep -q "depends_on:"; then
    pass "Service dependencies are defined"
else
    warn "No explicit service dependencies"
fi

# 7. Check for secrets in compose files
echo -e "\n🔒 Security check..."
if grep -rE "(password|secret|key):\s*['\"][^'\"]+['\"]" docker-compose*.yml > /dev/null 2>&1; then
    fail "Hardcoded secrets found in docker-compose files!"
else
    pass "No hardcoded secrets in compose files"
fi

# 8. Verify Dockerfiles exist
echo -e "\n🐳 Checking Dockerfiles..."
for dir in backend frontend; do
    if [ -f "$dir/Dockerfile" ]; then
        pass "$dir/Dockerfile exists"
    else
        fail "$dir/Dockerfile is missing"
    fi
done

# 9. Check port conflicts
echo -e "\n🔌 Checking for port conflicts..."
if command -v lsof > /dev/null 2>&1; then
    ports=("8000:backend" "3000:frontend" "5432:postgres" "6379:redis")
    for port_info in "${ports[@]}"; do
        port="${port_info%%:*}"
        service="${port_info##*:}"
        
        if lsof -i :$port > /dev/null 2>&1; then
            warn "Port $port ($service) is already in use on host"
        else
            pass "Port $port ($service) is available"
        fi
    done
else
    warn "lsof command not available, skipping port conflict checks"
fi

# Summary
echo -e "\n📊 Validation Summary"
echo "===================="
echo -e "${GREEN}Passed:${NC} $check_passed"
echo -e "${RED}Failed:${NC} $check_failed"

if [ $check_failed -eq 0 ]; then
    echo -e "\n${GREEN}✅ Docker stack is production-ready!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Docker stack has issues that need attention${NC}"
    exit 1
fi
