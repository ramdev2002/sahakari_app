from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.identity.permissions import IsStaffUser

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, IsStaffUser]
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        queryset = AuditLog.objects.select_related('actor').order_by('-occurred_at')
        entity_type = self.request.query_params.get('entity_type')
        entity_id = self.request.query_params.get('entity_id')
        action = self.request.query_params.get('action')
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)
        if entity_id:
            queryset = queryset.filter(entity_id=entity_id)
        if action:
            queryset = queryset.filter(action=action)
        return queryset
