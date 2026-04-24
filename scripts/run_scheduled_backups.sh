#!/usr/bin/env bash
# Intended for cron: dump DB + media, then optionally `rclone copy` to RCLONE_REMOTE.
# Run from anywhere; changes to repo root. Requires `docker compose` and running stack.
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

./scripts/backup_db.sh
./scripts/backup_media.sh

if [[ -n "${RCLONE_REMOTE:-}" ]]; then
  if ! command -v rclone >/dev/null 2>&1; then
    echo "RCLONE_REMOTE is set but rclone is not installed." >&2
    exit 1
  fi
  dest="${BACKUP_DIR:-./backups}"
  echo "rclone copy \"$dest\" -> \"$RCLONE_REMOTE\""
  rclone copy "$dest" "$RCLONE_REMOTE" --progress --retries 3 --low-level-retries 10
fi

echo "Scheduled backup finished at $(date -Iseconds)"
