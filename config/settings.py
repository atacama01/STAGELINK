"""
Internship Management service settings (STAGELINK, Member 4).

Every environment-specific value comes from an environment variable. Nothing
secret is hard-coded, so the repository can be shared with the team as-is.
See .env.example for the full list and service.md section 2 for the rationale.
"""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    POSTGRES_PORT=(int, 5432),
    MAX_UPLOAD_SIZE_BYTES=(int, 10 * 1024 * 1024),
    MAX_FILES_PER_SUBMISSION=(int, 5),
    MAX_LINKS_PER_SUBMISSION=(int, 5),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "internships",
    "submissions",
    "notifications",
    "audit",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="internship_db"),
        "USER": env("POSTGRES_USER", default="stagelink"),
        "PASSWORD": env("POSTGRES_PASSWORD", default=""),
        "HOST": env("POSTGRES_HOST", default="localhost"),
        "PORT": env("POSTGRES_PORT"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Algiers"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Files (service.md section 8) ------------------------------------------
# MEDIA_ROOT is a local directory in development and a persistent volume in
# deployment. It must never be exposed by the web server: files are served
# only through authorized endpoints.
MEDIA_ROOT = env("MEDIA_ROOT", default=str(BASE_DIR / "media"))
MAX_UPLOAD_SIZE_BYTES = env("MAX_UPLOAD_SIZE_BYTES")
# Proposed limits, pending the team decision in project.md item 7.
MAX_FILES_PER_SUBMISSION = env("MAX_FILES_PER_SUBMISSION")
MAX_LINKS_PER_SUBMISSION = env("MAX_LINKS_PER_SUBMISSION")

# --- JWT validation (service.md section 2) ---------------------------------
# This service only validates tokens; Identity & Profiles issues them. The
# algorithm and claim names are a team decision (project.md items 1 and 2)
# and must match what Identity & Profiles signs with.
JWT_ALGORITHM = env("JWT_ALGORITHM", default="HS256")
JWT_SECRET = env("JWT_SECRET", default=None)
JWT_PUBLIC_KEY = env("JWT_PUBLIC_KEY", default=None)
JWT_ACCESS_TOKEN_LIFETIME = timedelta(minutes=env.int("JWT_ACCESS_MINUTES", default=30))

# --- Service-to-service auth (service.md section 5) ------------------------
# Shared token for /api/internal/ endpoints, compared in constant time.
INTERNAL_SERVICE_TOKEN = env("INTERNAL_SERVICE_TOKEN", default=None)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "common.jwt_auth.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "common.pagination.DefaultPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "common.exceptions.api_exception_handler",
    "UNAUTHENTICATED_USER": None,
}
