import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse

from dotenv import dotenv_values, load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env.local")
load_dotenv(BASE_DIR / ".env")
file_env = dotenv_values(BASE_DIR / ".env.local")
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-change-this-secret")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = [host.strip() for host in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost,app-scrapper.fly.dev,app-scrapper-v7fb.onrender.com").split(",") if host.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "reviews",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"

DATABASE_URL = os.getenv("DATABASE_URL") or file_env.get("DATABASE_URL", "")
if DATABASE_URL.startswith("sqlite://"):
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": DATABASE_URL.removeprefix("sqlite://")}}
elif DATABASE_URL:
    parsed = urlparse(DATABASE_URL)
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": parsed.path.removeprefix("/"),
        "USER": parsed.username,
        "PASSWORD": parsed.password,
        "HOST": parsed.hostname,
        "PORT": parsed.port or 5432,
    }}
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,https://app-scrapper.fly.dev,https://app-scrapper.joashkuteesa223.workers.dev").split(",") if origin.strip()]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "http://localhost:5173,https://app-scrapper.fly.dev,https://app-scrapper.joashkuteesa223.workers.dev").split(",") if origin.strip()]
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework_simplejwt.authentication.JWTAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}
SIMPLE_JWT = {"ACCESS_TOKEN_LIFETIME": timedelta(minutes=60), "REFRESH_TOKEN_LIFETIME": timedelta(days=7)}
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
