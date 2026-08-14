from pathlib import Path
import os

from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key


BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None

if load_dotenv:
    load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}

WEASYPRINT_DLL_DIRECTORIES = [
    item
    for item in [
        os.getenv("WEASYPRINT_DLL_DIRECTORIES"),
        str(BASE_DIR / "runtime" / "weasyprint" / "bin"),
        r"C:\msys64\mingw64\bin",
        r"C:\msys64\ucrt64\bin",
    ]
    if item and Path(item).exists()
]
if WEASYPRINT_DLL_DIRECTORIES:
    os.environ["WEASYPRINT_DLL_DIRECTORIES"] = os.pathsep.join(WEASYPRINT_DLL_DIRECTORIES)
    if hasattr(os, "add_dll_directory"):
        for directory in WEASYPRINT_DLL_DIRECTORIES:
            try:
                os.add_dll_directory(directory)
            except OSError:
                pass

DEBUG = env_bool("DJANGO_DEBUG", True)
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("Defina DJANGO_SECRET_KEY no ambiente antes de iniciar o Celeris.")
    SECRET_KEY = get_random_secret_key()
ALLOWED_HOSTS = [item.strip() for item in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if item.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.accounts",
    "apps.core",
    "apps.atendimento",
    "apps.estoque",
    "apps.reports",
    "apps.tickets",
    "apps.social",
    "apps.enfermagem",
    "apps.ti",
    "apps.pesquisas",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.accounts.middleware.ScreenAccessMiddleware",
    "apps.core.middleware.SessionActivityMiddleware",
    "apps.core.middleware.SecurityHeadersMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "celeris.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.navigation",
            ],
        },
    },
]

WSGI_APPLICATION = "celeris.wsgi.application"

DB_ENGINE = os.getenv("CELERIS_DB_ENGINE", "sqlite").lower()
if DB_ENGINE == "mysql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("CELERIS_DB_NAME", "celeris"),
            "USER": os.getenv("CELERIS_DB_USER", "root"),
            "PASSWORD": os.getenv("CELERIS_DB_PASSWORD", ""),
            "HOST": os.getenv("CELERIS_DB_HOST", "localhost"),
            "PORT": os.getenv("CELERIS_DB_PORT", "3306"),
            "OPTIONS": {"charset": "utf8mb4"},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / os.getenv("CELERIS_DB_NAME", "db.sqlite3"),
        }
    }

AUTH_USER_MODEL = "accounts.User"
LANGUAGE_CODE = "pt-br"
TIME_ZONE = os.getenv("CELERIS_TIME_ZONE", "America/Sao_Paulo")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "core:home"
LOGOUT_REDIRECT_URL = "login"
SESSION_COOKIE_AGE = 900
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_FAILURE_VIEW = "apps.accounts.views.csrf_failure"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_SSL_REDIRECT = env_bool("CELERIS_SECURE_SSL_REDIRECT", not DEBUG)
SESSION_COOKIE_SECURE = env_bool("CELERIS_SESSION_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_SECURE = env_bool("CELERIS_CSRF_COOKIE_SECURE", not DEBUG)
SECURE_HSTS_SECONDS = int(
    os.getenv("CELERIS_SECURE_HSTS_SECONDS", "31536000" if not DEBUG else "0")
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("CELERIS_SECURE_HSTS_INCLUDE_SUBDOMAINS", not DEBUG)
SECURE_HSTS_PRELOAD = env_bool("CELERIS_SECURE_HSTS_PRELOAD", not DEBUG)
if env_bool("CELERIS_TRUST_PROXY_SSL_HEADER", False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv("CELERIS_DATA_UPLOAD_MAX_MEMORY_SIZE", "25000000"))
CELERIS_CERTIFICATE_MASTER_KEY = os.getenv("CELERIS_CERTIFICATE_MASTER_KEY", "")
CELERIS_CERTIFICATE_MASTER_KEY_VERSION = os.getenv("CELERIS_CERTIFICATE_MASTER_KEY_VERSION", "v1")
CELERIS_CERTIFICATE_MAX_UPLOAD_SIZE = int(os.getenv("CELERIS_CERTIFICATE_MAX_UPLOAD_SIZE", "10485760"))
CELERIS_CERTIFICATE_EXPIRY_WARNING_DAYS = int(os.getenv("CELERIS_CERTIFICATE_EXPIRY_WARNING_DAYS", "30"))
CELERIS_CERTIFICATE_EXPIRY_WARNING_LEVELS = tuple(
    sorted(
        {
            int(value)
            for value in os.getenv("CELERIS_CERTIFICATE_EXPIRY_WARNING_LEVELS", "60,30,15,7,1").split(",")
            if value.strip().isdigit()
        },
        reverse=True,
    )
)
CELERIS_TSA_URL = os.getenv("CELERIS_TSA_URL", "").strip()
CELERIS_TSA_TIMEOUT = int(os.getenv("CELERIS_TSA_TIMEOUT", "10"))

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

CACHES = {
    "default": {
        "BACKEND": os.getenv("CELERIS_CACHE_BACKEND", "django.core.cache.backends.locmem.LocMemCache"),
        "LOCATION": os.getenv("CELERIS_CACHE_LOCATION", "celeris-default"),
        "TIMEOUT": 300,
    }
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "celeris_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "celeris.log",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "detailed",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "celeris": {
            "handlers": ["celeris_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
