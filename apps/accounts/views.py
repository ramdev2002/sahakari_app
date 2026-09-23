from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.identity.permissions import IsSuperUserOrAdministrativeOfficer

from .models import Account, AccountBalance, AccountType
from .serializers import AccountBalanceSerializer, AccountSerializer, AccountTypeSerializer


class AccountTypeViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AccountTypeSerializer
    queryset = AccountType.objects.filter(status='active').order_by('code')
    search_fields = ['code', 'name']
    ordering_fields = ['code', 'name']


class AccountViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AccountSerializer
    search_fields = ['account_no', 'name']
    ordering_fields = ['account_no', 'name', 'status']

    def get_queryset(self):
        queryset = Account.objects.select_related('account_type', 'branch', 'member').filter(
            status='active'
        )
        member = self.request.query_params.get('member')
        branch = self.request.query_params.get('branch')
        if member:
            queryset = queryset.filter(member_id=member)
        if branch:
            queryset = queryset.filter(branch_id=branch)
        return queryset

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsSuperUserOrAdministrativeOfficer()]
        return [IsAuthenticated()]

    def perform_destroy(self, instance):
        instance.soft_delete()


class AccountBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AccountBalanceSerializer
    search_fields = ['account__account_no']
    ordering_fields = ['current_balance', 'available_balance']

    def get_queryset(self):
        queryset = AccountBalance.objects.select_related('account').all()
        account = self.request.query_params.get('account')
        if account:
            queryset = queryset.filter(account__account_no=account)
        return queryset
