from rest_framework import serializers

from .models import SavingsAccount, SavingsProduct


class SavingsProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavingsProduct
        fields = [
            'id',
            'code',
            'name',
            'interest_rate',
            'min_opening_balance',
            'status',
            'is_deleted',
            'deleted_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['is_deleted', 'deleted_at', 'created_at', 'updated_at']


class SavingsAccountSerializer(serializers.ModelSerializer):
    member = serializers.CharField(source='member.member_no', read_only=True)
    member_name = serializers.SerializerMethodField()
    product = serializers.CharField(source='product.code', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    branch = serializers.CharField(source='branch.code', read_only=True, allow_null=True)
    current_balance = serializers.DecimalField(
        max_digits=20, decimal_places=2, source='account.balance.current_balance', read_only=True
    )

    class Meta:
        model = SavingsAccount
        fields = [
            'id',
            'account_no',
            'member',
            'member_name',
            'product',
            'product_name',
            'account',
            'branch',
            'opened_on',
            'status',
            'current_balance',
            'is_deleted',
            'deleted_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['is_deleted', 'deleted_at', 'created_at', 'updated_at']

    def get_member_name(self, obj):
        return f'{obj.member.first_name} {obj.member.last_name}'.strip()


class SavingsAccountCreateSerializer(serializers.Serializer):
    member = serializers.UUIDField()
    product = serializers.UUIDField()
    initial_deposit = serializers.DecimalField(
        max_digits=20, decimal_places=2, required=False, default=0
    )
    idempotency_key = serializers.CharField(max_length=64, required=False, allow_blank=True)
