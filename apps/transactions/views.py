from rest_framework import status as http_status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.core.permissions import (
    CanDeposit,
    CanReverse,
    CanTransfer,
    CanViewTransactions,
    CanWithdraw,
)

from . import services
from .models import Transaction
from .serializers import (
    DepositSerializer,
    ReverseSerializer,
    TransactionSerializer,
    TransferSerializer,
    WithdrawSerializer,
)


class TransactionViewSet(ReadOnlyModelViewSet):
    """Read-only view of transactions plus service action endpoints."""

    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer
    search_fields = ['reference', 'kind', 'status', 'memo']
    ordering_fields = ['-created_at']

    def get_queryset(self):
        queryset = Transaction.objects.select_related('requested_by', 'branch').order_by(
            '-created_at'
        )
        status = self.request.query_params.get('status')
        kind = self.request.query_params.get('kind')
        branch = self.request.query_params.get('branch')
        if status:
            queryset = queryset.filter(status=status)
        if kind:
            queryset = queryset.filter(kind=kind)
        if branch:
            queryset = queryset.filter(branch_id=branch)
        return queryset

    def get_permissions(self):
        action_permissions = {
            'deposit': CanDeposit,
            'withdraw': CanWithdraw,
            'transfer': CanTransfer,
            'reverse': CanReverse,
        }
        permission_cls = action_permissions.get(self.action, CanViewTransactions)
        return [IsAuthenticated(), permission_cls()]

    @classmethod
    def service_kwargs(cls, serializer_data, request):
        kwargs = {
            'branch': getattr(request.user, 'branch', None),
            'requested_by': None if request.user.is_anonymous else request.user,
            'source_channel': 'api',
        }
        if serializer_data.get('idempotency_key'):
            kwargs['idempotency_key'] = serializer_data['idempotency_key']
        if serializer_data.get('memo'):
            kwargs['memo'] = serializer_data['memo']
        return kwargs

    @action(detail=False, methods=['post'])
    def deposit(self, request):
        serializer = DepositSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            tx = services.deposit(
                account=serializer.validated_data['account'],
                amount=serializer.validated_data['amount'],
                **self.service_kwargs(serializer.validated_data, request),
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(TransactionSerializer(tx).data, status=http_status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def withdraw(self, request):
        serializer = WithdrawSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            tx = services.withdraw(
                account=serializer.validated_data['account'],
                amount=serializer.validated_data['amount'],
                **self.service_kwargs(serializer.validated_data, request),
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(TransactionSerializer(tx).data, status=http_status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def transfer(self, request):
        serializer = TransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            tx = services.transfer(
                from_account=serializer.validated_data['from_account'],
                to_account=serializer.validated_data['to_account'],
                amount=serializer.validated_data['amount'],
                **self.service_kwargs(serializer.validated_data, request),
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(TransactionSerializer(tx).data, status=http_status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def reverse(self, request, pk=None):
        transaction = self.get_object()
        serializer = ReverseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            tx = services.reverse(
                transaction=transaction,
                reason=serializer.validated_data.get('reason', ''),
                requested_by=self.request.user,
                idempotency_key=serializer.validated_data.get('idempotency_key'),
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(TransactionSerializer(tx).data, status=http_status.HTTP_201_CREATED)
