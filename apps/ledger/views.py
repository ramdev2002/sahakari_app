from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Journal, LedgerEntry
from .serializers import JournalSerializer, LedgerEntrySerializer


class JournalViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = JournalSerializer
    search_fields = ['journal_no', 'description', 'reference']
    ordering_fields = ['created_at', 'journal_no']

    def get_queryset(self):
        queryset = (
            Journal.objects.select_related('transaction')
            .prefetch_related('entries__account')
            .order_by('-created_at')
        )
        transaction = self.request.query_params.get('transaction')
        if transaction:
            queryset = queryset.filter(transaction__reference=transaction)
        return queryset


class LedgerEntryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = LedgerEntrySerializer
    search_fields = ['account__account_no', 'note', 'journal__journal_no']
    ordering_fields = ['journal__created_at']

    def get_queryset(self):
        queryset = LedgerEntry.objects.select_related('account', 'journal').order_by(
            'journal__created_at'
        )
        account = self.request.query_params.get('account')
        if account:
            queryset = queryset.filter(account__account_no=account)
        return queryset
