from django.core.exceptions import ImproperlyConfigured

from .base import *

DEBUG = False

# Production must always provide an explicit secret key (see base.py guard).
SECRET_KEY = env('DJANGO_SECRET_KEY')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured('ALLOWED_HOSTS must be set in production via DJANGO_ALLOWED_HOSTS.')

CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

# Only trusted origins are allowed for CORS in production.
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
CORS_ALLOW_ALL_ORIGINS = False

# ---------------------------------------------------------------------------
# HTTPS / security hardening
# ---------------------------------------------------------------------------
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'

# Serve static files through the web server (nginx/caddy) in production.
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# WhiteNoise serves compressed, fingerprinted static assets from the app process.
MIDDLEWARE.insert(2, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATIC_ROOT = env('STATIC_ROOT', default=str(BASE_DIR / 'staticfiles'))
STORAGES = {'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'}}
