import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
env = os.environ.get

SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-insecure-key")
DEBUG = env("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "rest_framework",
    "accounts",
    "documents",
    "chat",
]
MIDDLEWARE = ["django.middleware.common.CommonMiddleware"]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "zesp"),
        "USER": env("POSTGRES_USER", "zesp"),
        "PASSWORD": env("POSTGRES_PASSWORD", "zesp"),
        "HOST": env("POSTGRES_HOST", "db"),
        "PORT": env("POSTGRES_PORT", "5432"),
    }
}
AUTH_USER_MODEL = "accounts.User"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LANGUAGE_CODE = "pl"
TIME_ZONE = "Europe/Warsaw"
USE_TZ = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
    ],
}
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

MEDIA_ROOT = env("MEDIA_ROOT", str(BASE_DIR / "media"))
CHROMA_PATH = env("CHROMA_PATH", str(BASE_DIR / "chroma"))
MAX_PDF_BYTES = int(env("MAX_PDF_MB", "20")) * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_PDF_BYTES + 1024 * 1024

# --- LLM / RAG ---
LLM_API_KEY = env("API_KEY", "")
LLM_BASE_URL = env("LLM_BASE_URL", "https://openrouter.ai/api/v1")
CHAT_MODEL = env("CHAT_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free")
EMBEDDING_MODEL = env("EMBEDDING_MODEL", "nvidia/nemotron-3-embed-1b:free")
LLM_TIMEOUT = float(env("LLM_TIMEOUT", "60"))
LLM_RETRIES = 2
LLM_RETRY_BACKOFF = float(env("LLM_RETRY_BACKOFF", "2"))
EMBED_BATCH_SIZE = 32
SIMILARITY_THRESHOLD = float(env("SIMILARITY_THRESHOLD", "0.23"))
TOP_K = 5
CHUNK_SIZE = (800, 1000)
CHUNK_OVERLAP = 150
