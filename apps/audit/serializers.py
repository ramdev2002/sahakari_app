from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor = serializers.CharField(source='actor.username', read_only=True, allow_null=True)

    class Meta:
        model = AuditLog
        fields = [
            'id',
            'actor',
            'action',
            'entity_type',
            'entity_id',
            'summary',
            'detail',
            'occurred_at',
        ]
        read_only_fields = fields
