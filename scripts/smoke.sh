#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"

echo "[1/6] Backend health"
curl -sf "${BASE_URL}/health" | cat
echo

echo "[2/6] DB migrations"
docker compose exec -T backend alembic upgrade head

echo "[3/6] Dev bootstrap admin"
curl -sf -X POST "${BASE_URL}/auth/dev/bootstrap" | cat
echo

echo "[4/6] Create a test cooperative (admin token)"
TOKEN=$(curl -sf -X POST "${BASE_URL}/auth/login" -H "Content-Type: application/json" -d '{"email":"admin@local","password":"adminadmin"}' | python -c 'import sys, json; print(json.load(sys.stdin)["access_token"])')

curl -sf -X POST "${BASE_URL}/cooperatives/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name":"SmokeTest Coop","region":"Cajamarca","altitude_m":1600,"contact_email":"test@example.com"}' | cat
echo

echo "[5/6] Run discovery dry-run (requires PERPLEXITY_API_KEY; will skip if missing)"
if docker compose exec -T backend python -c 'import os; import sys; sys.exit(0 if os.getenv("PERPLEXITY_API_KEY") else 1)'; then
  TASK_ID=$(curl -sf -X POST "${BASE_URL}/discovery/seed" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"entity_type":"both","max_entities":10,"dry_run":true}' | python -c 'import sys, json; print(json.load(sys.stdin)["task_id"])')
  echo "task_id=${TASK_ID}"
  sleep 2
  curl -sf "${BASE_URL}/discovery/seed/${TASK_ID}" -H "Authorization: Bearer ${TOKEN}" | cat
  echo
else
  echo "PERPLEXITY_API_KEY nicht gesetzt -> Discovery Smoke übersprungen."
fi

echo "[6/6] Done."