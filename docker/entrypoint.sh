#!/bin/sh
set -eu

if [ "${1-}" = "uvicorn" ]; then
  echo "Running database migrations before starting the API..."
  alembic upgrade head
fi

exec "$@"