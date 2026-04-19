#!/bin/sh
set -e

echo "Waiting for PostgreSQL to become available..."
python /app/scripts/wait_for_postgres.py

echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
