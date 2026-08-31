import logging

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger('apps')


def custom_exception_handler(exc, context):
    """Convert DRF and uncaught exceptions into a consistent JSON shape."""

    # Let DRF handle its own exceptions (validation, auth, not-found, etc.).
    response = exception_handler(exc, context)

    if response is not None:
        # Normalise DRF errors into a stable {"detail": ...} top-level shape
        # so clients can parse failures uniformly across endpoints.
        data = {
            'detail': response.data.get('detail', 'Request failed.'),
            'errors': response.data,
        }
        return Response(data, status=response.status_code)

    # Unhandled exception -> log the full traceback, then return a generic
    # 500 response (never leak internals to the client).
    logger.exception(
        'Unhandled exception in %s: %s',
        context.get('view').__class__.__name__ if context.get('view') else 'view',
        exc,
    )

    detail = 'Internal server error.'
    if settings.DEBUG:
        detail = f'{exc.__class__.__name__}: {exc}'

    return Response(
        {'detail': detail, 'errors': None},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
