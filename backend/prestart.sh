#!/bin/bash

# Let migrations run directly (depends_on healthcheck handles DB readiness)

# Wait for Postgres
echo "Waiting for PostgreSQL to start..."
sleep 15

# Run migrations
alembic upgrade head

# Start Uvicorn
echo "Starting Uvicorn..."
exec uvicorn server:app --host 0.0.0.0 --port 8001
