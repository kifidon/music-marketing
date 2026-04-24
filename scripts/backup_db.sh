#!/usr/bin/env bash
# Dump Postgres from the `db` service in docker-compose.yml to a SQL file on the host.
# Run from the repo root (same directory as docker-compose.yml).
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

: "${POSTGRES_USER:=music}"
: "${POSTGRES_PASSWORD:=music}"
: "${POSTGRES_DB:=music}"

out_dir="${BACKUP_DIR:-./backups}"
mkdir -p "$out_dir"
stamp="$(date +%Y%m%d-%H%M%S)"
out_file="${out_dir}/${POSTGRES_DB}-${stamp}.sql.gz"

echo "Writing $out_file"
docker compose exec -T db \
  env PGPASSWORD="$POSTGRES_PASSWORD" \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  --no-owner --clean --if-exists \
  | gzip -9 > "$out_file"

echo "Done. Copy this file somewhere safe (S3, another machine, laptop)."
