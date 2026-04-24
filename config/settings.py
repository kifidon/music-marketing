import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-not-for-production")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
# If set, visiting /s/<slug>/?reset_gate=<this value> clears the fan-gate session for that song.
SMARTLINKS_RESET_GATE_SECRET = os.environ.get("SMARTLINKS_RESET_GATE_SECRET", "").strip()
SERVE_UPLOADS = os.environ.get("SERVE_UPLOADS", "0") == "1"
ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]

_csrf_raw = os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").strip()
CSRF_TRUST_ALL_ORIGINS = _csrf_raw == "*"
if CSRF_TRUST_ALL_ORIGINS:
    CSRF_TRUSTED_ORIGINS = []
else:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_raw.split(",") if o.strip()]


def _postgres_from_url(url: str) -> dict:
    """Build Django DATABASES['default'] from a postgres / postgresql URL (e.g. Supabase)."""
    from urllib.parse import parse_qs, unquote, urlparse

    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    name = (parsed.path or "/postgres").lstrip("/") or "postgres"
    cfg = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": name,
        "USER": parsed.username or "postgres",
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "localhost",
        "PORT": str(parsed.port or 5432),
    }
    sslmode = (qs.get("sslmode") or [None])[0]
    if sslmode:
        cfg["OPTIONS"] = {"sslmode": sslmode}
    return cfg


def database_from_env():
    """
    Local (``DJANGO_DEBUG=1``): always SQLite at ``BASE_DIR / db.sqlite3`` — ``DATABASE_URL`` is ignored.

    Production (``DJANGO_DEBUG=0``): requires a Postgres ``DATABASE_URL`` (e.g. Supabase).
    """
    from django.core.exceptions import ImproperlyConfigured

    if DEBUG:
        return {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": str(BASE_DIR / "db.sqlite3"),
            }
        }

    url = os.environ.get("DATABASE_URL", "").strip()
    if not url or url.startswith("sqlite"):
        raise ImproperlyConfigured(
            "Production (DJANGO_DEBUG=0) requires a Postgres DATABASE_URL such as your Supabase "
            "connection string. Local development uses SQLite automatically when DJANGO_DEBUG=1."
        )
    return {"default": _postgres_from_url(url)}


DATABASES = database_from_env()

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "users",
    "smartlinks",
]

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

AUTH_USER_MODEL = "users.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "config.csrf_middleware.RelaxedCsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

CELERY_TIMEZONE = TIME_ZONE

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "smartlinks:dashboard"
LOGOUT_REDIRECT_URL = "smartlinks:home"

if DEBUG:
    STORAGES["staticfiles"] = {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    }
