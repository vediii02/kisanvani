#!/bin/bash

# Improved prestart script for Kisan Vani AI
set -e

# Wait for Postgres to be ready for queries
echo "Waiting for PostgreSQL to be ready..."
# Extract host and port from environment or use defaults
DB_HOST=${PG_HOST:-kisanvani_postgres}
DB_PORT=${PG_PORT:-5432}

# Use a simple netcat check until pg_isready is available or just loop
MAX_RETRIES=30
RETRY_COUNT=0

until nc -z "$DB_HOST" "$DB_PORT" || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
  echo "PostgreSQL is unavailable - sleeping..."
  sleep 2
  RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
  echo "Error: PostgreSQL did not become ready in time."
  exit 1
fi

echo "PostgreSQL is up - starting migrations..."

# Run migrations
alembic upgrade head

# Start Server based on APP_ENV
if [ "$APP_ENV" = "production" ]; then
    echo "Starting Gunicorn in production mode..."
    exec gunicorn server:app \
        --workers 4 \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind 0.0.0.0:8001 \
        --timeout 120 \
        --access-loglevel info
else
    echo "Starting Uvicorn with reload for development..."
    exec uvicorn server:app --host 0.0.0.0 --port 8001 --reload --reload-dir /app
fi

