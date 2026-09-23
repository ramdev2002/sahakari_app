from rest_framework import serializers

from .models import Account, AccountBalance, AccountType


class AccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountType
        fields = [
            'id',
            'code',
            'name',
            'side',
            'category',
            'is_system',
            'status',
            'is_deleted',
            'deleted_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['is_deleted', 'deleted_at', 'created_at', 'updated_at']


class AccountSerializer(serializers.ModelSerializer):
    account_type_code = serializers.CharField(source='account_type.code', read_only=True)
    branch_code = serializers.CharField(source='branch.code', read_only=True, allow_null=True)

    class Meta:
        model = Account
        fields = [
            'id',
            'account_no',
            'name',
            'account_type',
            'account_type_code',
            'member',
            'branch',
            'branch_code',
            'allows_overdraft',
            'status',
            'is_deleted',
            'deleted_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['is_deleted', 'deleted_at', 'created_at', 'updated_at']


class AccountBalanceSerializer(serializers.ModelSerializer):
    account = serializers.CharField(source='account.account_no', read_only=True)

    class Meta:
        model = AccountBalance
        fields = ['id', 'account', 'current_balance', 'available_balance', 'updated_at']
        read_only_fields = fields
