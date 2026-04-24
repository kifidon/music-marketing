#!/usr/bin/env bash
# One-shot: copy BACKUP_DIR to RCLONE_REMOTE only (no new dump). Useful after manual dumps.
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

: "${RCLONE_REMOTE:?Set RCLONE_REMOTE in .env (e.g. b2:bucket/prefix)}"

src="${BACKUP_DIR:-./backups}"
rclone copy "$src" "$RCLONE_REMOTE" --progress --retries 3 --low-level-retries 10
