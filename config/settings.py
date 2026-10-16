# ==============================================================================
# config/settings.py
# SISMOC-CUMBE | Configuración Principal de Django
# Empresa de Transportes El Cumbe S.A.C. — RUC: 20480397731
# ==============================================================================

import os
from pathlib import Path
from dotenv import load_dotenv

# Directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables de entorno desde .env
load_dotenv(BASE_DIR / ".env")

# Seguridad
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-dev-key-change-in-production")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver,*").split(",")


# ==============================================================================
# APLICACIONES INSTALADAS
# ==============================================================================
INSTALLED_APPS = [
    # Django Core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Terceros
    "corsheaders",
    "ninja",

    # Apps del Proyecto SISMOC-CUMBE
    "core.apps.CoreConfig",
    "asistencia.apps.AsistenciaConfig",
]


# ==============================================================================
# MIDDLEWARE
# ==============================================================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"


# ==============================================================================
# TEMPLATES
# ==============================================================================
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
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# ==============================================================================
# BASE DE DATOS
# ==============================================================================
DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.getenv("DB_NAME", str(BASE_DIR / "sismoc_cumbe_db.sqlite3")),
        "USER": os.getenv("DB_USER", ""),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", ""),
        "PORT": os.getenv("DB_PORT", ""),
    }
}


# ==============================================================================
# MODELO DE USUARIO PERSONALIZADO (RBAC 7 Roles)
# ==============================================================================
AUTH_USER_MODEL = "core.Usuario"


# ==============================================================================
# VALIDACIÓN DE CONTRASEÑAS
# ==============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ==============================================================================
# INTERNACIONALIZACIÓN (Perú)
# ==============================================================================
LANGUAGE_CODE = "es-pe"
TIME_ZONE = "America/Lima"
USE_I18N = True
USE_TZ = True


# ==============================================================================
# ARCHIVOS ESTÁTICOS Y MEDIA (Subida de Excel y Fotos de Peajes)
# ==============================================================================
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"


# ==============================================================================
# CONFIGURACIÓN DE DJANGO NINJA (API)
# ==============================================================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ==============================================================================
# CORS (Para permitir conexión desde la App Móvil / PWA)
# ==============================================================================
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Solo en desarrollo
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


# ==============================================================================
# CONFIGURACIÓN DEL HUELLERO ZKTECO
# ==============================================================================
ZKTECO_CONFIG = {
    "IP": os.getenv("ZKTECO_IP", "192.168.1.201"),
    "PORT": int(os.getenv("ZKTECO_PORT", "4370")),
    "TIMEOUT": 5,  # Segundos de espera para conexión
}
