#!/usr/bin/env sh
# One container: Gunicorn + Celery worker (e.g. single Render web service).
set -e
cd /app
python manage.py migrate --noinput
trap 'kill 0' TERM INT
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers "${GUNICORN_WORKERS:-2}" &
celery -A config worker --loglevel="${CELERY_LOG_LEVEL:-INFO}" &
wait
