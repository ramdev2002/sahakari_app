from rest_framework import serializers

from .models import Journal, LedgerEntry


class LedgerEntrySerializer(serializers.ModelSerializer):
    account = serializers.CharField(source='account.account_no', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)

    class Meta:
        model = LedgerEntry
        fields = ['id', 'journal', 'account', 'account_name', 'debit', 'credit', 'note']
        read_only_fields = fields


class JournalSerializer(serializers.ModelSerializer):
    entries = LedgerEntrySerializer(many=True, read_only=True)
    transaction = serializers.CharField(
        source='transaction.reference', read_only=True, allow_null=True
    )

    class Meta:
        model = Journal
        fields = [
            'id',
            'journal_no',
            'transaction',
            'description',
            'reference',
            'created_at',
            'updated_at',
            'entries',
        ]
        read_only_fields = ['journal_no', 'created_at', 'updated_at']
