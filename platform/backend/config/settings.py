import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "development-only-never-use-in-production")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
if not DEBUG and SECRET_KEY == "development-only-never-use-in-production":
    raise RuntimeError("Set DJANGO_SECRET_KEY in production")
ALLOWED_HOSTS = os.environ.get(
    "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver,backend"
).split(",")
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "core",
    "catalog",
    "crm",
    "sales",
    "accounting",
    "treasury",
    "operations",
    "documents",
    "payroll",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "core.middleware.AuditActorMiddleware",
    "core.middleware.AdminLoginThrottleMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("DJANGO_SQLITE_PATH", BASE_DIR / "db.sqlite3"),
    }
}
if os.environ.get("POSTGRES_HOST"):
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": os.environ["POSTGRES_HOST"],
        "NAME": os.environ.get("POSTGRES_DB", "karma"),
        "USER": os.environ.get("POSTGRES_USER", "karma"),
        "PASSWORD": os.environ["POSTGRES_PASSWORD"],
    }
LANGUAGE_CODE = "fa-ir"
TIME_ZONE = "Asia/Tehran"
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
]
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.AnonRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"anon": "120/min"},
}
ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL", "")
CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

REST_FRAMEWORK["DEFAULT_SCHEMA_CLASS"] = "drf_spectacular.openapi.AutoSchema"
SPECTACULAR_SETTINGS = {
    "TITLE": "Karma Platform API",
    "VERSION": "2.0.0-alpha.1",
    "SERVE_PERMISSIONS": ["rest_framework.permissions.IsAdminUser"],
}

if os.environ.get("REDIS_URL"):
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": os.environ.get(
                "KARMA_CACHE_URL", os.environ["REDIS_URL"].rsplit("/", 1)[0] + "/1"
            ),
        }
    }

CSRF_TRUSTED_ORIGINS = (
    os.environ.get(
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000" if DEBUG else "",
    ).split(",")
    if (DEBUG or os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS"))
    else []
)

MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

CELERY_TASK_DEFAULT_QUEUE = os.environ.get("KARMA_TASK_QUEUE", "karma")

REST_FRAMEWORK["DEFAULT_PARSER_CLASSES"] = [
    "core.parsers.ExactJSONParser",
    "rest_framework.parsers.FormParser",
    "rest_framework.parsers.MultiPartParser",
]

if not DEBUG and not os.environ.get("POSTGRES_HOST"):
    raise RuntimeError("Production financial storage requires PostgreSQL")
