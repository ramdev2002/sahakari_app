from rest_framework import serializers

from .models import Loan, LoanProduct


class LoanProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanProduct
        fields = [
            'id',
            'code',
            'name',
            'min_amount',
            'max_amount',
            'interest_rate',
            'default_tenure_months',
            'status',
            'is_deleted',
            'deleted_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['is_deleted', 'deleted_at', 'created_at', 'updated_at']


class LoanSerializer(serializers.ModelSerializer):
    member = serializers.CharField(source='member.member_no', read_only=True)
    product = serializers.CharField(source='product.code', read_only=True)
    savings_account = serializers.CharField(source='savings_account.account_no', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Loan
        fields = [
            'id',
            'loan_no',
            'member',
            'product',
            'savings_account',
            'principal',
            'interest_rate',
            'tenure_months',
            'status',
            'status_display',
            'disbursed_at',
            'principal_paid',
            'interest_paid',
            'outstanding_principal',
            'outstanding_interest',
            'total_interest',
            'created_at',
            'updated_at',
            'is_deleted',
            'deleted_at',
        ]
        read_only_fields = [
            'loan_no',
            'status',
            'disbursed_at',
            'principal_paid',
            'interest_paid',
            'outstanding_principal',
            'outstanding_interest',
            'total_interest',
            'created_at',
            'updated_at',
            'is_deleted',
            'deleted_at',
        ]


class LoanCreateSerializer(serializers.Serializer):
    member = serializers.UUIDField()
    product = serializers.UUIDField()
    savings_account = serializers.UUIDField()
    principal = serializers.DecimalField(max_digits=20, decimal_places=2)


class LoanActionSerializer(serializers.Serializer):
    idempotency_key = serializers.CharField(max_length=64, required=False, allow_blank=True)
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)


class LoanRepaySerializer(LoanActionSerializer):
    amount = serializers.DecimalField(max_digits=20, decimal_places=2)
