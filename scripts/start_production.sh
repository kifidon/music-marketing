#!/usr/bin/env sh
# Gunicorn only (e.g. single Render web service).
set -e
cd /app
python manage.py migrate --noinput
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers "${GUNICORN_WORKERS:-2}"
