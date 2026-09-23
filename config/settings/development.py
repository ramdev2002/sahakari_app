from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# Use a fast hasher locally to keep development password hashing snappy.
# Production (production.py) keeps Django's secure PBKDF2 default.
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]

# Permit arbitrary origins during development. Override via CORS_ALLOWED_ORIGINS
# in production (see base.py).
CORS_ALLOW_ALL_ORIGINS = True

# Always show the full stack trace for unhandled errors in dev.
DEBUG_PROPAGATE_EXCEPTIONS = False

# Serve rendered emails to the console instead of sending them.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
