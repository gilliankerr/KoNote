#!/bin/sh
set -e

echo "Running migrations..."
python manage.py migrate --noinput 2>&1 || echo "Migration failed, continuing..."

echo "Running audit migrations..."
python manage.py migrate --database=audit --noinput 2>&1 || echo "Audit migration failed, continuing..."

echo "Seeding data..."
python manage.py seed 2>&1 || echo "Seed failed, continuing..."

echo "Starting gunicorn on port 8000"
exec gunicorn konote.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 120 \
    --log-level info \
    --error-logfile - \
    --access-logfile -
