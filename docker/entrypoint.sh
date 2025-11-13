#!/bin/sh
set -eu

if [ "${1-}" = "uvicorn" ]; then
  echo "Running database migrations before starting the API..."
  alembic upgrade head

  echo "Checking for DB seed script..."
  if [ -f "src/res/init-db.sql" ]; then
    echo "Running DB seed from src/res/init-db.sql..."
    PGPASSWORD="${POSTGRES_PASSWORD:-}" psql \
      -h "${POSTGRES_HOST:-postgres}" \
      -p "${POSTGRES_PORT:-5432}" \
      -U "${POSTGRES_USER:-guest}" \
      -d "${POSTGRES_DB:-guest}" \
      -v ON_ERROR_STOP=1 \
      -f "src/res/init-db.sql"
    echo "DB seed completed."
  else
    echo "Seed file src/res/init-db.sql not found, skipping..."
  fi
fi

exec "$@"
