#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${REPO_ROOT}/.env"

get_env_value() {
  local key="$1"
  if [[ ! -f "${ENV_FILE}" ]]; then
    return 1
  fi
  grep -E "^${key}=" "${ENV_FILE}" | head -n1 | cut -d= -f2-
}

BOOTSTRAP_ADMIN_EMAIL="${BOOTSTRAP_ADMIN_EMAIL:-$(get_env_value BOOTSTRAP_ADMIN_EMAIL || true)}"
BOOTSTRAP_ADMIN_PASSWORD="${BOOTSTRAP_ADMIN_PASSWORD:-$(get_env_value BOOTSTRAP_ADMIN_PASSWORD || true)}"

if [[ -z "${BOOTSTRAP_ADMIN_EMAIL}" || -z "${BOOTSTRAP_ADMIN_PASSWORD}" ]]; then
  echo "BOOTSTRAP_ADMIN_EMAIL/BOOTSTRAP_ADMIN_PASSWORD fehlen. Fuehre zuerst run_windows.ps1 aus oder setze die Werte in .env." >&2
  exit 1
fi

echo "[1/5] Backend health"
curl -sf "${BASE_URL}/health" | cat
echo

echo "[2/5] DB migrations"
docker compose exec -T backend alembic upgrade head

echo "[3/5] Dev bootstrap admin"
curl -sf -X POST "${BASE_URL}/auth/dev/bootstrap" | cat
echo

echo "[4/5] Admin login"
TOKEN="$(
  curl -sf -X POST "${BASE_URL}/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"${BOOTSTRAP_ADMIN_EMAIL}\",\"password\":\"${BOOTSTRAP_ADMIN_PASSWORD}\"}" \
    | python -c 'import sys, json; print(json.load(sys.stdin)["access_token"])'
)"

echo "[5/5] Authenticated cooperative listing"
curl -sf -X GET "${BASE_URL}/cooperatives/" \
  -H "Authorization: Bearer ${TOKEN}" | cat
echo

echo "SMOKE OK"
