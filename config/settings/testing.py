from .base import *

DEBUG = False

ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']

# Fast password hashing keeps CI/local test suites quick. The hash algorithm is
# irrelevant here because only hashing speed matters in tests; production
# settings keep PBKDF2.
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# No throttling in tests so limits never interfere with test suites.
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {}

# Do not send real emails during tests.
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Keep logs quiet during test runs unless a test explicitly asserts on them.
LOGGING['root']['handlers'] = ['console']
