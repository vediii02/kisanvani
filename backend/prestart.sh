#!/bin/bash

# Let migrations run directly (depends_on healthcheck handles DB readiness)

# Run migrations
echo "Running Alembic migrations..."
alembic upgrade head

# Start Uvicorn
echo "Starting Uvicorn..."
exec uvicorn server:app --host 0.0.0.0 --port 8001
