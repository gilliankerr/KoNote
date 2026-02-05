#!/bin/sh
set -e

echo "Running migrations..."
python manage.py migrate --noinput
echo "Migrations complete."

echo "Running audit migrations..."
python manage.py migrate --database=audit --noinput
echo "Audit migrations complete."

# Seed runs all sub-commands in the right order:
# metrics, features, settings, event types, note templates, intake fields,
# demo data (if DEMO_MODE), and demo client field values
echo ""
echo "Seeding data..."
python manage.py seed 2>&1 || echo "WARNING: Seed failed (see error above). App will start but may be missing data."

# Security check before starting the application
# Set KONOTE_MODE=demo to allow startup with security warnings (for evaluation)
# Set KONOTE_MODE=production (default) to block startup if security checks fail
echo ""
echo "Running security checks..."
python manage.py startup_check
# If startup_check exits non-zero, the script stops here (set -e)

PORT=${PORT:-8000}
echo "Starting gunicorn on port $PORT"
exec gunicorn konote.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --log-level info \
    --error-logfile - \
    --access-logfile -
