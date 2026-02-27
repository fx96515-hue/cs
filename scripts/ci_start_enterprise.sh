#!/usr/bin/env bash
set -euo pipefail

# CI-friendly script to start the enterprise compose stack and run basic health checks.
# Usage: ./scripts/ci_start_enterprise.sh [compose-file] [health-url]
# Defaults: compose-file=infra/deploy/docker-compose.enterprise.yml, health-url=http://localhost:8000/health

COMPOSE_FILE="${1:-infra/deploy/docker-compose.enterprise.yml}"
HEALTH_URL="${2:-http://localhost:8000/health}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-120}"

echo "Using compose file: $COMPOSE_FILE"
echo "Health URL: $HEALTH_URL"
echo "Timeout: ${TIMEOUT_SECONDS}s"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker not found in PATH" >&2
  exit 2
fi

if [ ! -f "$COMPOSE_FILE" ]; then
  echo "Compose file not found: $COMPOSE_FILE" >&2
  exit 3
fi

# Ensure env file(s) referenced by the enterprise compose exist.
COMPOSE_DIR="$(cd "$(dirname "$COMPOSE_FILE")" && pwd)"
CANDIDATES=(
  "$COMPOSE_DIR/../env/enterprise.env"
  "$COMPOSE_DIR/../env/enterprise.env.example"
)

found_env=""
for f in "${CANDIDATES[@]}"; do
  if [ -f "$f" ]; then
    found_env="$f"
    break
  fi
done

if [ -n "$found_env" ]; then
  echo "Found enterprise env file: $found_env"
else
  # Best-effort fallback: create a SAFE placeholder env in the compose-expected location
  fallback="$COMPOSE_DIR/../env/enterprise.env"
  echo "Warning: no enterprise env found. Creating fallback: $fallback"
  mkdir -p "$(dirname "$fallback")"
  cat > "$fallback" <<'EOF'
# Enterprise environment (auto-generated fallback, NO secrets)
DATABASE_URL=postgresql+psycopg://coffeestudio:changeme@postgres:5432/coffeestudio
REDIS_URL=redis://redis:6379/0
JWT_SECRET=replace-with-a-secure-secret-of-at-least-32-chars
CORS_ORIGINS=http://localhost:3000
PERPLEXITY_API_KEY=
EOF
fi

docker compose -f "$COMPOSE_FILE" up --build -d

deadline=$((SECONDS + TIMEOUT_SECONDS))
echo -n "Waiting for health endpoint"
while [ $SECONDS -lt $deadline ]; do
  if curl -sSf --max-time 5 "$HEALTH_URL" >/dev/null 2>&1; then
    echo " -> ok"
    break
  fi
  echo -n "."
  sleep 2
done

if [ $SECONDS -ge $deadline ]; then
  echo -e "\nHealth endpoint did not respond within ${TIMEOUT_SECONDS}s" >&2
  echo "Container logs:" >&2
  docker compose -f "$COMPOSE_FILE" logs --no-color --tail=200 >&2 || true
  exit 4
fi

check_port() {
  host=${1:-localhost}
  port=${2}
  # try /dev/tcp (bash builtin) if available
  if (exec 3<>/dev/tcp/${host}/${port}) >/dev/null 2>&1; then
    exec 3>&-
    return 0
  fi
  return 1
}

echo "Checking TCP ports: postgres(5432), redis(6379)"
if ! check_port localhost 5432; then
  echo "Postgres port 5432 not open on localhost" >&2
  docker compose -f "$COMPOSE_FILE" logs postgres --no-color --tail=200 >&2 || true
  exit 5
fi

if ! check_port localhost 6379; then
  echo "Redis port 6379 not open on localhost" >&2
  docker compose -f "$COMPOSE_FILE" logs redis --no-color --tail=200 >&2 || true
  exit 6
fi

echo "All basic checks passed."
echo "CI can proceed with tests or further integration steps."
exit 0
