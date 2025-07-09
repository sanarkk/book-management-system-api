#!/bin/sh

echo "Waiting for PostgreSQL to be ready"
until pg_isready -h db -p 5432 -U "$POSTGRES_USER"; do
  sleep 1
done

echo "DB is ready"

if [ -z "$(ls -A alembic/versions 2>/dev/null)" ]; then
  echo "No migration scripts found, generating initial migration"
  alembic revision --autogenerate -m "create initial tables"
else
  echo "Migration scripts found, skipping revision generation"
fi

echo "Running Alembic migrations"
alembic upgrade head

echo "Starting FastAPI"
exec uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 2 --reload
