from django.db import connection
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@extend_schema(
    responses={
        200: OpenApiResponse(
            inline_serializer(
                'HealthResponse',
                fields={
                    'status': serializers.CharField(),
                    'database': serializers.CharField(),
                    'environment': serializers.CharField(),
                },
            ),
            description='Service health',
        )
    },
    description='Liveness/readiness probe (no auth required).',
)
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Liveness/readiness probe. Returns 200 when DB is reachable."""
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False
    from django.conf import settings

    return Response(
        {
            'status': 'ok' if db_ok else 'degraded',
            'database': 'ok' if db_ok else 'error',
            'environment': getattr(settings, 'ENVIRONMENT_NAME', 'unknown'),
        },
        status=200 if db_ok else 503,
    )
