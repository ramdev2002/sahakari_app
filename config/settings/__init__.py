import os

from .base import *

ENVIRONMENT = os.environ.get(
    'DJANGO_ENVIRONMENT', os.environ.get('ENVIRONMENT', 'development')
).lower()

if ENVIRONMENT == 'production':
    from .production import *
elif ENVIRONMENT in ('testing', 'test'):
    from .testing import *
else:
    from .development import *
