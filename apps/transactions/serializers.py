from rest_framework import serializers

from apps.accounts.models import Account

from .models import Transaction


class AccountField(serializers.PrimaryKeyRelatedField):
    def __init__(self, **kwargs):
        super().__init__(queryset=Account.objects.filter(status='active'), **kwargs)


class DepositSerializer(serializers.Serializer):
    account = AccountField()
    amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    idempotency_key = serializers.CharField(max_length=64, required=False, allow_blank=True)
    memo = serializers.CharField(max_length=255, required=False, allow_blank=True)


class WithdrawSerializer(serializers.Serializer):
    account = AccountField()
    amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    idempotency_key = serializers.CharField(max_length=64, required=False, allow_blank=True)
    memo = serializers.CharField(max_length=255, required=False, allow_blank=True)


class TransferSerializer(serializers.Serializer):
    from_account = AccountField()
    to_account = AccountField()
    amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    idempotency_key = serializers.CharField(max_length=64, required=False, allow_blank=True)
    memo = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs['from_account'].pk == attrs['to_account'].pk:
            raise serializers.ValidationError('From and to accounts must differ.')
        return attrs


class ReverseSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)
    idempotency_key = serializers.CharField(max_length=64, required=False, allow_blank=True)


class TransactionSerializer(serializers.ModelSerializer):
    kind_display = serializers.CharField(source='get_kind_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    channel_display = serializers.CharField(source='get_source_channel_display', read_only=True)
    branch = serializers.CharField(source='branch.code', read_only=True, allow_null=True)
    requested_by = serializers.CharField(
        source='requested_by.username', read_only=True, allow_null=True
    )

    class Meta:
        model = Transaction
        fields = [
            'id',
            'reference',
            'kind',
            'kind_display',
            'status',
            'status_display',
            'source_channel',
            'channel_display',
            'idempotency_key',
            'requested_by',
            'branch',
            'memo',
            'error_message',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'reference', 'status', 'created_at', 'updated_at']
