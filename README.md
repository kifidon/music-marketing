# Music smart links (Django)

Personal smart-link landing pages with a fan opt-in gate, Postgres-ready schema, and basic analytics tables.

Auth uses a custom **`users.User`** model (`AbstractUser`). Extend `users.models.User` and run `makemigrations`. Elsewhere, use `django.contrib.auth.get_user_model()` instead of importing `User` from `django.contrib.auth.models`.

## Database

- **`DJANGO_DEBUG=1`:** Django always uses **`db.sqlite3`** (ignores `DATABASE_URL`). For local dev only.
- **`DJANGO_DEBUG=0`:** requires Postgres **`DATABASE_URL`** (e.g. Supabase).

## Run locally (SQLite fallback)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .prod.env .env
# Local SQLite: set DJANGO_DEBUG=1 in `.env` (prod template uses DJANGO_DEBUG=0).
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

To use Postgres on your machine instead, set `DATABASE_URL` in `.env` (same shape as in Docker) and run migrations against that DB.

- Admin: `http://127.0.0.1:8000/admin/` — create songs, upload cover art, set platform URLs and accent color. You can paste a **one-time distro / presave smart link** in **Import from smart link** on a song; on save the app fetches the page and fills Spotify / Apple / YouTube / etc. URLs it can find in the HTML (best-effort; JS-only pages may need manual URLs).
- Public landing: `http://127.0.0.1:8000/s/<slug>/`
- Staff dashboard: `http://127.0.0.1:8000/me/` (after login)

## Docker (Postgres)

```bash
export DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(50))')"
docker compose up --build
```

`SERVE_UPLOADS=1` is enabled in Compose so Django serves `/media/` for quick testing. On a VM with Nginx, serve `/media/` from disk and turn `SERVE_UPLOADS` off.

## Analytics (rough definitions)

- **Landing loads** — rows in `analytics_landing_page_views` (includes repeats; use `session_key` or time windows if you want “unique sessions”).
- **Click-through** — rows in `analytics_outbound_link_clicks` after unlock.
- **CTR (per song)** — `click_count / view_count` with whatever dedupe rule you prefer.
- **Gate submissions** — `analytics_fan_gate_submissions` logs each successful submit (valid email).

## Oracle / own domain

Run the `web` container (or Gunicorn) behind Nginx, proxy to port 8000, set `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` to your domain, keep Postgres on the same host or managed instance, and persist the `media` volume (or local path) for cover art.

## Environment (secrets, not in git)

Keep a private **`.prod.env`** (see `.gitignore`; do not commit filled secrets). For Docker Compose, copy it to **`.env`** in the repo root so Compose can substitute variables. Set at least **`DJANGO_SECRET_KEY`**, **`DATABASE_URL`** (Supabase), **`DJANGO_ALLOWED_HOSTS`**, and **`DJANGO_CSRF_TRUSTED_ORIGINS`** for production.

## Backups (do not rely on the VM disk alone)

Your data lives in two places: **Postgres** (`pgdata` volume) and **uploaded cover art** (`media` volume). If the VM dies without off-server copies, you can lose both.

**1. Database — logical dumps (`pg_dump`)**

On the server, from this repo (with containers running):

```bash
chmod +x scripts/*.sh
./scripts/backup_db.sh
```

Scripts **`source .env`** when present so they use the same `POSTGRES_*` as Compose. Output goes to **`BACKUP_DIR`** (default `./backups/`, ignored by git).

**2. Media files**

```bash
./scripts/backup_media.sh
```

**3. Off-site sync with rclone**

1. On the VM: [install rclone](https://rclone.org/install/) and run **`rclone config`** once to create a remote (Backblaze B2, S3, Google Drive, etc.).
2. In **`.env`**, set for example:
   - `BACKUP_DIR=/var/backups/music-marketing`
   - `RCLONE_REMOTE=b2:my-bucket/music-marketing` (remote name and path from `rclone config listremotes`)

3. Run everything (dump + optional upload):

```bash
./scripts/run_scheduled_backups.sh
```

To upload existing dumps only:

```bash
./scripts/sync_backups_rclone.sh
```

**4. Cron example (daily 03:15 UTC)**

```cron
15 3 * * * cd /path/to/music-marketing && /usr/bin/env bash -lc './scripts/run_scheduled_backups.sh' >> /var/log/music-marketing-backup.log 2>&1
```

Use the real repo path on the server and ensure the cron user can run **`docker compose`** (often add that user to the `docker` group).

**5. Restore (Postgres)**

From the repo, with `.env` loaded so passwords match:

```bash
set -a && source .env && set +a
gunzip -c "$BACKUP_DIR/music-YYYYMMDD-HHMMSS.sql.gz" | docker compose exec -T db env PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

**6. What not to do for Postgres**

Avoid copying the raw `pgdata` directory while Postgres is running unless you know how to take a consistent filesystem snapshot. **`pg_dump`** (or `pg_basebackup`, or managed-DB snapshots) is safer.

**7. Production habits**

- Remove or firewall **`5432`** on the VM if you do not need host access to Postgres.
- Test a **restore** on a scratch DB once so the procedure still works.
