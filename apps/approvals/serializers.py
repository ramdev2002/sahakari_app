from rest_framework import serializers

from .models import ApprovalRequest, ApprovalRule


class ApprovalRequestSerializer(serializers.ModelSerializer):
    requested_by = serializers.CharField(
        source='requested_by.username', read_only=True, allow_null=True
    )
    reviewed_by = serializers.CharField(
        source='reviewed_by.username', read_only=True, allow_null=True
    )

    class Meta:
        model = ApprovalRequest
        fields = [
            'id',
            'entity_type',
            'entity_id',
            'action',
            'requested_by',
            'status',
            'reviewed_by',
            'reviewed_at',
            'note',
            'review_comment',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'requested_by',
            'status',
            'reviewed_by',
            'reviewed_at',
            'created_at',
            'updated_at',
        ]


class ApprovalDecisionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=['approved', 'rejected'])
    comment = serializers.CharField(max_length=500, required=False, allow_blank=True)


class ApprovalCreateSerializer(serializers.Serializer):
    entity_type = serializers.CharField(max_length=100)
    entity_id = serializers.CharField(max_length=64)
    action = serializers.CharField(max_length=50)
    note = serializers.CharField(max_length=500, required=False, allow_blank=True)


class ApprovalRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalRule
        fields = ['id', 'action', 'role', 'is_active']
