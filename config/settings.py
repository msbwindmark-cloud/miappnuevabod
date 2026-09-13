"""
Configuración de Chill Out La Bodeguita - Django 5.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env', override=True)

print('=== EMAIL CONFIG ===')
print('EMAIL_HOST:', os.environ.get('EMAIL_HOST'))
print('EMAIL_PORT:', os.environ.get('EMAIL_PORT'))
print('EMAIL_HOST_USER:', os.environ.get('EMAIL_HOST_USER'))
print('EMAIL_HOST_PASSWORD:', (os.environ.get('EMAIL_HOST_PASSWORD') or '')[:6] + '***')
print('DEFAULT_FROM_EMAIL:', os.environ.get('DEFAULT_FROM_EMAIL'))
print('EMAIL_NOTIFY_TO:', os.environ.get('EMAIL_NOTIFY_TO'))
print('=== END EMAIL CONFIG ===')

def env(key, default=None):
    return os.environ.get(key, default)

# Seguridad
SECRET_KEY = env('SECRET_KEY', 'django-insecure-xgzjv7+_jezdfn9rj(r70)l0%+)+rsf#=**$zca^qa*z5np0j^')
DEBUG = env('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = [h for h in env('ALLOWED_HOSTS', '127.0.0.1,localhost,testserver,miappnuevabod.pythonanywhere.com').split(',') if h]

INSTALLED_APPS = [
    'core.apps.CoreConfig',
    'livereload',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Apps del dominio
    'caja',
    'inventario',
    'pedidos',
    'auditoria',
]

MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'core.middleware.AuditoriaRequestMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if DEBUG:
    MIDDLEWARE.insert(1, 'livereload.middleware.LiveReloadScript')

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.global_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'Europe/Madrid'
USE_I18N = True
USE_TZ = True

# Static y media
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Autenticación potente
LOGIN_URL = 'core:login'
LOGIN_REDIRECT_URL = 'core:home'
LOGOUT_REDIRECT_URL = 'core:login'
SESSION_COOKIE_AGE = 60 * 60 * 8          # 8 horas
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_SSL_REDIRECT = True

# Límite de intentos de login
LOGIN_MAX_ATTEMPTS = int(env('LOGIN_MAX_ATTEMPTS', '5'))
LOGIN_LOCK_MINUTES = int(env('LOGIN_LOCK_MINUTES', '30'))

# Notificaciones por email
EMAIL_BACKEND = 'django.core.mail.backends.{}'.format(
    env('EMAIL_BACKEND', 'console.EmailBackend')
)
EMAIL_HOST = env('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(env('EMAIL_PORT', '587'))
EMAIL_USE_TLS = env('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_USE_SSL = env('EMAIL_USE_SSL', 'False') == 'True'
EMAIL_HOST_USER = env('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', 'Chill Out La Bodeguita <no-reply@bodeguita.local>')
EMAIL_NOTIFY_TO = [e for e in env('EMAIL_NOTIFY_TO', '').split(',') if e]

# Configuración de la aplicación
EMPRESA = 'Chill Out La Bodeguita'
EMPRESA_CIUDAD = 'Cabra (Córdoba)'
COPAS_POR_BOTELLA = int(env('COPAS_POR_BOTELLA', '8'))