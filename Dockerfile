FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# With ``DJANGO_DEBUG=0``, ``DATABASE_URL`` must be available at image build (e.g. build-arg / CI env).
RUN chmod +x scripts/start_production.sh \
    && DJANGO_DEBUG=0 DJANGO_SECRET_KEY=collectstatic-placeholder \
    python manage.py collectstatic --noinput \
    && python manage.py migrate --noinput 

EXPOSE 8000

CMD ["scripts/start_production.sh"]
