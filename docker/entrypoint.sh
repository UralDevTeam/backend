#!/bin/sh
set -eu

POSTGRES_HOST="${POSTGRES__HOST:-${POSTGRES_HOST:-postgres}}"
POSTGRES_PORT="${POSTGRES__PORT:-${POSTGRES_PORT:-5432}}"
POSTGRES_DB="${POSTGRES__DB_NAME:-${POSTGRES_DB:-guest}}"
POSTGRES_USER="${POSTGRES__USER:-${POSTGRES_USER:-guest}}"
POSTGRES_PASSWORD="${POSTGRES__PASSWORD:-${POSTGRES_PASSWORD:-}}"

if [ "${1-}" = "uvicorn" ]; then
  echo "Running database migrations before starting the API..."
  alembic upgrade head

  echo "Checking for DB seed script..."
  if [ -f "src/res/init-db.sql" ]; then
    echo "Running DB seed from src/res/init-db.sql..."
    PGPASSWORD="${POSTGRES_PASSWORD}" psql \
      -h "${POSTGRES_HOST}" \
      -p "${POSTGRES_PORT}" \
      -U "${POSTGRES_USER}" \
      -d "${POSTGRES_DB}" \
      -v ON_ERROR_STOP=1 \
      -f "src/res/init-db.sql"
    echo "DB seed completed."
  else
    echo "Seed file src/res/init-db.sql not found, skipping..."
  fi
fi

exec "$@"
