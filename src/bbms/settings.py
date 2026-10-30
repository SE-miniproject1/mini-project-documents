"""Settings for the Blood Bank Management System.

Configuration comes from environment variables so that no secret is ever
committed (SRS SI-1). See `.env.example` for the full list.
"""

import os
import sys
from decimal import Decimal
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
    "accounts",
    "core",
    "donors",
    "collection",
    "inventory",
    "bloodrequests",
    "audit",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # SRS NFR-SEC1: every view needs a signed-in user unless it opts out with
    # @login_not_required (login, password reset, registration, health probe).
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
    "audit.middleware.CurrentRequestMiddleware",
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
                "core.context_processors.navigation",
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
    "loggers": {"pyBarcode": {"level": "WARNING"}},  # only SVG output is used
}

# ---------------------------------------------------------------------------
# Authentication and sessions (SRS section 6.3)
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = ["accounts.backends.LockoutBackend"]
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "accounts:login"

# NFR-SEC3: at least 10 characters with a letter, a digit and a special character,
# and no password from the common-password (known-compromised) list.
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    {"NAME": "accounts.validators.ComplexityValidator"},
]

# NFR-SEC2: Django's default PBKDF2-SHA256 with a per-password salt is a deliberately slow
# key derivation function. Only the automated tests swap it for a fast hasher.
TESTING = "test" in sys.argv
if TESTING:
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# NFR-SEC4: lock for 15 minutes after 5 consecutive failures.
BBMS_LOCKOUT_THRESHOLD = 5
BBMS_LOCKOUT_MINUTES = 15

# NFR-SEC11: sessions expire after 30 minutes of inactivity. Saving on every request makes
# the expiry slide with activity. Logout flushes the session and a password change
# invalidates every other session through Django's session auth hash.
SESSION_COOKIE_AGE = 30 * 60
SESSION_SAVE_EVERY_REQUEST = True

# SRS CI-1 and CI-3: Secure, HttpOnly, SameSite=Lax cookies, HTTPS only, HSTS. Switched on in
# production, where Nginx terminates TLS and forwards X-Forwarded-Proto.
SECURE_DEPLOYMENT = env_bool("BBMS_SECURE", ENVIRONMENT == "production")
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = SECURE_DEPLOYMENT
CSRF_COOKIE_SECURE = SECURE_DEPLOYMENT
SECURE_SSL_REDIRECT = SECURE_DEPLOYMENT
SECURE_HSTS_SECONDS = 31536000 if SECURE_DEPLOYMENT else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_DEPLOYMENT
if SECURE_DEPLOYMENT:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Email: the console in development; an SMTP relay over STARTTLS in production (SRS SI-3).
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@bbms.local")
if ENVIRONMENT == "production":
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.environ.get("EMAIL_HOST", "localhost")
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
    EMAIL_USE_TLS = True
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ---------------------------------------------------------------------------
# Donor eligibility rules (SRS REQ-6, REQ-8, BR-2, BR-3)
# ---------------------------------------------------------------------------
# Held here until the administrator configuration screen (US-26, REQ-46) exists. Decimals
# keep every comparison exact, as NFR-Q4 requires.
BBMS_ELIGIBILITY = {
    "min_age": 18,
    "max_age": 65,
    "min_weight_kg": Decimal("50"),
    "min_haemoglobin": Decimal("12.5"),
    "min_systolic": 100,
    "max_systolic": 140,
    "donation_interval_days": 90,
    # How long a physical-criteria deferral (weight, haemoglobin, blood pressure) lasts
    # before the donor is re-evaluated. The SRS does not state a figure.
    "deferral_review_days": 30,
}

# Shelf life in days from collection, by component (SRS BR-4).
BBMS_SHELF_LIFE_DAYS = {
    "Whole Blood": 35,
    "PRBC": 42,
    "FFP": 365,
    "Platelets": 5,
    "Cryoprecipitate": 365,
}

# Where a unit is shelved when it is released from quarantine. Staff can move it later (REQ-21).
BBMS_DEFAULT_STORAGE_LOCATION = "FRIDGE-A1"

# Available units this close to their expiry date are flagged and listed in the daily digest
# (SRS REQ-20). Held here until the configuration screen exists (US-26).
BBMS_NEAR_EXPIRY_DAYS = 7

# Components a whole blood unit can be separated into (SRS REQ-15), with where each is shelved
# and a typical volume to suggest on the form.
BBMS_SEPARATION = {
    "PRBC": {"storage": "FRIDGE-A1", "suggested_ml": 200},
    "FFP": {"storage": "FREEZER-B1", "suggested_ml": 150},
    "Platelets": {"storage": "PLATELET-AGITATOR-1", "suggested_ml": 50},
}
