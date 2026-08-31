import os

from .base import *

ENVIRONMENT = os.environ.get('ENVIRONMENT', 'local')

if ENVIRONMENT == 'production':
    from .production import *
else:
    from .local import *
