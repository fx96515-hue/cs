#!/usr/bin/env bash
set -euo pipefail

# Comprehensive integration smoke test for a running local stack.
# Exits with 0 on success and 1 if any required check fails.

BASE_URL="${BASE_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
MAX_RETRIES="${MAX_RETRIES:-30}"
RETRY_DELAY="${RETRY_DELAY:-2}"
ENV_FILE="${ENV_FILE:-.env}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0
FAILED_TESTS=()
TOKEN=""

log_section() {
  echo
  echo -e "${BLUE}========================================${NC}"
  echo -e "${BLUE}$1${NC}"
  echo -e "${BLUE}========================================${NC}"
}

log_info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

log_pass() {
  echo -e "${GREEN}[PASS]${NC} $1"
  ((PASS_COUNT++))
}

log_fail() {
  echo -e "${RED}[FAIL]${NC} $1"
  FAILED_TESTS+=("$1")
  ((FAIL_COUNT++))
}

log_skip() {
  echo -e "${YELLOW}[SKIP]${NC} $1"
  ((SKIP_COUNT++))
}

get_env_value() {
  local key="$1"
  if [[ ! -f "${ENV_FILE}" ]]; then
    return 1
  fi

  local line
  line="$(grep -E "^${key}=" "${ENV_FILE}" | head -n1 || true)"
  if [[ -z "${line}" ]]; then
    return 1
  fi

  echo "${line#*=}"
}

wait_for_url() {
  local name="$1"
  local url="$2"
  local attempts=0

  log_info "Waiting for ${name} at ${url}"
  while [[ "${attempts}" -lt "${MAX_RETRIES}" ]]; do
    if curl -fsS "${url}" >/dev/null 2>&1; then
      log_pass "${name} reachable"
      return 0
    fi
    attempts=$((attempts + 1))
    sleep "${RETRY_DELAY}"
  done

  log_fail "${name} not reachable after ${MAX_RETRIES} retries"
  return 1
}

test_api() {
  local name="$1"
  local method="$2"
  local endpoint="$3"
  local expected_status="$4"
  local payload="${5:-}"
  local auth_mode="${6:-none}"

  local auth_header=()
  if [[ "${auth_mode}" == "bearer" && -n "${TOKEN}" ]]; then
    auth_header=(-H "Authorization: Bearer ${TOKEN}")
  fi

  local response
  if [[ -n "${payload}" ]]; then
    response="$(curl -sS -w "\n%{http_code}" -X "${method}" \
      "${BASE_URL}${endpoint}" \
      -H "Content-Type: application/json" \
      "${auth_header[@]}" \
      -d "${payload}" 2>&1 || true)"
  else
    response="$(curl -sS -w "\n%{http_code}" -X "${method}" \
      "${BASE_URL}${endpoint}" \
      "${auth_header[@]}" 2>&1 || true)"
  fi

  local status body
  status="$(echo "${response}" | tail -n1)"
  body="$(echo "${response}" | sed '$d')"

  if [[ "${status}" == "${expected_status}" ]]; then
    log_pass "${name} (HTTP ${status})"
    return 0
  fi

  log_fail "${name} (expected ${expected_status}, got ${status})"
  if [[ -n "${body}" ]]; then
    echo "  Body: ${body:0:300}"
  fi
  return 1
}

acquire_token() {
  local email password login_payload login_response

  email="${BOOTSTRAP_ADMIN_EMAIL:-$(get_env_value BOOTSTRAP_ADMIN_EMAIL || true)}"
  password="${BOOTSTRAP_ADMIN_PASSWORD:-$(get_env_value BOOTSTRAP_ADMIN_PASSWORD || true)}"

  if [[ -z "${email}" || -z "${password}" ]]; then
    log_skip "No BOOTSTRAP_ADMIN_EMAIL/BOOTSTRAP_ADMIN_PASSWORD in env or .env"
    return 1
  fi

  login_payload="{\"email\":\"${email}\",\"password\":\"${password}\"}"
  login_response="$(curl -sS -w "\n%{http_code}" -X POST \
    "${BASE_URL}/auth/login" \
    -H "Content-Type: application/json" \
    -d "${login_payload}" 2>&1 || true)"

  local status raw
  status="$(echo "${login_response}" | tail -n1)"
  raw="$(echo "${login_response}" | sed '$d')"

  if [[ "${status}" != "200" ]]; then
    log_fail "Admin login failed (HTTP ${status})"
    [[ -n "${raw}" ]] && echo "  Body: ${raw:0:300}"
    return 1
  fi

  if command -v python >/dev/null 2>&1; then
    TOKEN="$(echo "${raw}" | python -c 'import json,sys; print(json.load(sys.stdin).get("access_token",""))' 2>/dev/null || true)"
  else
    TOKEN="$(echo "${raw}" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')"
  fi

  if [[ -z "${TOKEN}" ]]; then
    log_fail "Could not parse access_token from login response"
    return 1
  fi

  log_pass "Admin login succeeded (token acquired)"
  return 0
}

main() {
  log_section "PHASE 1: Service Readiness"
  wait_for_url "Backend health" "${BASE_URL}/health" || true
  test_api "GET /health" "GET" "/health" "200" || true
  test_api "GET /metrics" "GET" "/metrics" "200" || true

  log_section "PHASE 2: Database Migration"
  if command -v docker >/dev/null 2>&1; then
    if docker compose ps backend >/dev/null 2>&1; then
      if docker compose exec -T backend alembic upgrade head >/dev/null 2>&1; then
        log_pass "Alembic migrations are up to date"
      else
        log_fail "Alembic migration check failed"
      fi
    else
      log_skip "backend container not available for migration check"
    fi
  else
    log_skip "docker not available for migration check"
  fi

  log_section "PHASE 3: Authentication"
  test_api "POST /auth/dev/bootstrap" "POST" "/auth/dev/bootstrap" "200" || true
  acquire_token || true

  log_section "PHASE 4: Core Authenticated APIs"
  if [[ -n "${TOKEN}" ]]; then
    test_api "GET /cooperatives" "GET" "/cooperatives" "200" "" "bearer" || true
    test_api "GET /roasters" "GET" "/roasters" "200" "" "bearer" || true
    test_api "GET /lots" "GET" "/lots" "200" "" "bearer" || true
    test_api "GET /shipments" "GET" "/shipments" "200" "" "bearer" || true
  else
    log_skip "Authenticated API checks skipped (no token)"
  fi

  log_section "PHASE 5: Frontend Reachability"
  local frontend_status
  frontend_status="$(curl -sS -o /dev/null -w "%{http_code}" "${FRONTEND_URL}" 2>/dev/null || true)"
  if [[ "${frontend_status}" == "200" || "${frontend_status}" == "304" ]]; then
    log_pass "Frontend reachable (${frontend_status})"
  elif [[ -z "${frontend_status}" || "${frontend_status}" == "000" ]]; then
    log_skip "Frontend not reachable (possibly not started)"
  else
    log_fail "Frontend returned unexpected status ${frontend_status}"
  fi

  log_section "SUMMARY"
  echo "PASS: ${PASS_COUNT}"
  echo "FAIL: ${FAIL_COUNT}"
  echo "SKIP: ${SKIP_COUNT}"

  if [[ "${FAIL_COUNT}" -gt 0 ]]; then
    echo
    echo "Failed tests:"
    for test_name in "${FAILED_TESTS[@]}"; do
      echo " - ${test_name}"
    done
    exit 1
  fi

  echo "Integration smoke test completed successfully."
}

main "$@"
