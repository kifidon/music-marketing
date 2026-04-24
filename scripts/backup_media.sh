#!/usr/bin/env bash
# Archive uploaded files from the web container (/app/media in docker-compose.yml).
# Run from the repo root with the stack up (or at least a container that has the volume).
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

out_dir="${BACKUP_DIR:-./backups}"
mkdir -p "$out_dir"
stamp="$(date +%Y%m%d-%H%M%S)"
out_file="${out_dir}/media-${stamp}.tar.gz"

echo "Writing $out_file (from service web:/app/media)"
docker compose exec -T web tar cz -C /app/media . | gzip -9 > "$out_file"

echo "Done."
