#!/usr/bin/env bash
set -euo pipefail

# CI-friendly script to start the enterprise compose stack and run basic health checks.
# Usage: ./scripts/ci_start_enterprise.sh [compose-file] [health-url]
# Defaults: compose-file=ops/deploy/docker-compose.enterprise.yml, health-url=http://localhost:8000/health

COMPOSE_FILE="${1:-ops/deploy/docker-compose.enterprise.yml}"
HEALTH_URL="${2:-http://localhost:8000/health}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-120}"

echo "Using compose file: $COMPOSE_FILE"
echo "Health URL: $HEALTH_URL"
echo "Timeout: ${TIMEOUT_SECONDS}s"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker not found in PATH" >&2
  exit 2
fi

# Ensure expected env file for compose exists. Many compose files reference an env at ops/.env.enterprise.example
COMPOSE_DIR=$(dirname "$COMPOSE_FILE")
EXPECTED_ENV="$COMPOSE_DIR/../.env.enterprise.example"
if [ -f "$EXPECTED_ENV" ]; then
  echo "Found expected env file: $EXPECTED_ENV"
elif [ -f .env.enterprise.example ]; then
  echo "Copying root .env.enterprise.example to $EXPECTED_ENV"
  mkdir -p "$(dirname "$EXPECTED_ENV")"
  cp .env.enterprise.example "$EXPECTED_ENV"
else
  echo "Warning: no .env.enterprise.example found in repo root or expected path. Creating empty $EXPECTED_ENV"
  mkdir -p "$(dirname "$EXPECTED_ENV")"
  touch "$EXPECTED_ENV"
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
  echo "\nHealth endpoint did not respond within ${TIMEOUT_SECONDS}s" >&2
  echo "Container logs:" >&2
  docker compose -f "$COMPOSE_FILE" logs --no-color --tail=200 >&2 || true
  exit 3
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
  docker compose -f "$COMPOSE_FILE" logs db --no-color --tail=100 || true
  exit 4
fi

if ! check_port localhost 6379; then
  echo "Redis port 6379 not open on localhost" >&2
  docker compose -f "$COMPOSE_FILE" logs redis --no-color --tail=100 || true
  exit 5
fi

echo "All basic checks passed."
echo "CI can proceed with tests or further integration steps."
exit 0
