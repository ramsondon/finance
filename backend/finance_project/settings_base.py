import os
from pathlib import Path

try:
    import environ  # type: ignore
except Exception:  # fallback shim
    class _SimpleEnv:
        def __call__(self, key, default=None):
            return os.environ.get(key, default)

        def list(self, key):
            v = os.environ.get(key)
            return [x for x in v.split(",") if x] if v else []

        def bool(self, key, default=False):
            v = os.environ.get(key)
            return v.lower() in ("1", "true", "yes") if isinstance(v, str) else default

    environ = None  # type: ignore
    Env = _SimpleEnv  # type: ignore
else:
    Env = environ.Env  # type: ignore

BASE_DIR = Path(__file__).resolve().parent.parent

env = Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_LOG_LEVEL=(str, "INFO"),
    DJANGO_ALLOWED_HOSTS=(list, ["*"]),
    TIME_ZONE=(str, "UTC"),
    OLLAMA_HOST=(str, "http://localhost:11434"),
    ACTIVE_AI_PROVIDER=(str, "ollama"),
    ALLOWLIST_ENABLED=(bool, False),
    CORS_ALLOWED_ORIGINS=(list, []),
    # POSTGRES_HOST=(str, "localhost"),
    # POSTGRES_PORT=(str, "5432"),
    # POSTGRES_USER=(str, "postgres"),
    # POSTGRES_PASSWORD=(str, ""),
    # POSTGRES_DB=(str, "finance"),
)

# Load defaults from deploy/.env.example when present
try:
    if environ:  # type: ignore
        environ.Env.read_env(os.path.join(BASE_DIR.parent, "deploy", ".env.example"))
except Exception:
    pass

SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-secret-key")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")
TIME_ZONE = env("TIME_ZONE")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "drf_spectacular",
    "django_filters",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "corsheaders",
    # Local apps
    "finance_project.apps.accounts",
    "finance_project.apps.banking",
    "finance_project.apps.analytics",
    "finance_project.apps.ai",
]

SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "finance_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "finance_project" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "finance_project.wsgi.application"
ASGI_APPLICATION = "finance_project.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="finance"),
        "USER": env("POSTGRES_USER", default="finance"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="finance"),
        "HOST": env("POSTGRES_HOST", default="localhost"),
        "PORT": env("POSTGRES_PORT", default="5432"),
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://localhost:6379/0"),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

# Allauth account settings
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_AUTHENTICATION_METHOD = "username_email"  # Allow both username and email login
ACCOUNT_EMAIL_REQUIRED = True  # Require email for signup
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True  # Ensure emails are unique
LOGIN_REDIRECT_URL = "/"

# Social account settings
SOCIALACCOUNT_AUTO_SIGNUP = True  # Automatically create account on first login
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_QUERY_EMAIL = True
# Store extra data from social provider
SOCIALACCOUNT_STORE_TOKENS = True

# Configure Google OAuth provider
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'VERIFIED_EMAIL': True,
    }
}

# Allauth adapter to enforce Google allowlist and customize username
SOCIALACCOUNT_ADAPTER = "finance_project.apps.accounts.auth.AllowlistSocialAccountAdapter"

# DRF
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ],
}
SPECTACULAR_SETTINGS = {
    "TITLE": "Finance API",
    "DESCRIPTION": "API for accounts, transactions, analytics, and AI insights.",
    "VERSION": "1.0.0",
}

# Static files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "finance_project" / "static"]

# WhiteNoise
WHITENOISE_MAX_AGE = 31536000

# Celery
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/1")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/2")
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_TIME_LIMIT = 300
CELERY_BEAT_SCHEDULE = {}

# Security baseline
SECURE_SSL_REDIRECT = bool(env.bool("DJANGO_SECURE_SSL_REDIRECT", default=False))
SESSION_COOKIE_SECURE = not bool(DEBUG)
CSRF_COOKIE_SECURE = not bool(DEBUG)
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript to read CSRF token
CSRF_USE_SESSIONS = False  # Use cookie-based CSRF tokens
CSRF_COOKIE_SAMESITE = 'Lax'  # Allow CSRF token in cross-origin requests
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# AI settings
ACTIVE_AI_PROVIDER = env("ACTIVE_AI_PROVIDER")
OLLAMA_HOST = env("OLLAMA_HOST")
ALLOWLIST_ENABLED = env("ALLOWLIST_ENABLED")

# CORS
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_ALL_ORIGINS = bool(DEBUG and not CORS_ALLOWED_ORIGINS)

# Defaults
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Basic logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {"handlers": ["console"], "level": env("DJANGO_LOG_LEVEL") },
}
