"""Settings for the Blood Bank Management System.

Configuration comes from environment variables so that no secret is ever
committed (SRS SI-1). See `.env.example` for the full list.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default):
    value = os.environ.get(name)
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


ENVIRONMENT = os.environ.get("BBMS_ENV", "development")
if ENVIRONMENT not in {"development", "test", "production"}:
    raise ImproperlyConfigured("BBMS_ENV must be development, test or production.")

DEBUG = env_bool("DJANGO_DEBUG", ENVIRONMENT == "development")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if ENVIRONMENT == "production":
        raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set in production.")
    # Fresh per process in development and tests, so no static key is ever committed.
    SECRET_KEY = get_random_secret_key()

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", ["localhost", "127.0.0.1", "testserver"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
]
AUTH_USER_MODEL = "core.User"
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "bbms.urls"

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

WSGI_APPLICATION = "bbms.wsgi.application"

# SQLite for development and the automated tests; PostgreSQL 15 in production (SRS OE-3).
if os.environ.get("DB_ENGINE") == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME", "bbms"),
            "USER": os.environ.get("DB_USER", "bbms"),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# SRS OR-3: timestamps are stored in UTC and shown in Asia/Kolkata, dates as DD-MM-YYYY.
LANGUAGE_CODE = "en"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True
DATE_FORMAT = "d-m-Y"
DATETIME_FORMAT = "d-m-Y H:i"
SHORT_DATE_FORMAT = "d-m-Y"
DATE_INPUT_FORMATS = ["%Y-%m-%d", "%d-%m-%Y"]

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# SRS OR-7: structured INFO logs for business events, ERROR for failures. Application code
# must never log passwords, session tokens or full medical histories.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "structured": {
            "format": "%(asctime)s level=%(levelname)s logger=%(name)s msg=%(message)s"
        },
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "structured"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
