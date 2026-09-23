from rest_framework import status as http_status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from apps.identity.permissions import IsSuperUserOrAdministrativeOfficer
from apps.members.models import Member

from . import services
from .models import Loan, LoanProduct
from .serializers import (
    LoanActionSerializer,
    LoanCreateSerializer,
    LoanProductSerializer,
    LoanRepaySerializer,
    LoanSerializer,
)


class LoanProductViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = LoanProductSerializer

    def get_queryset(self):
        return LoanProduct.objects.filter(status='active').order_by('code')

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsSuperUserOrAdministrativeOfficer()]
        return [IsAuthenticated()]

    def perform_destroy(self, instance):
        instance.soft_delete()


class LoanViewSet(GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = LoanSerializer

    def get_queryset(self):

        queryset = Loan.objects.select_related('member', 'product', 'savings_account').order_by(
            '-created_at'
        )
        status = self.request.query_params.get('status')
        member = self.request.query_params.get('member')
        if status:
            queryset = queryset.filter(status=status)
        if member:
            queryset = queryset.filter(member_id=member)
        return queryset

    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        instance = self.get_object()
        return Response(self.get_serializer(instance).data)

    @action(detail=False, methods=['post'])
    def create_loan(self, request):
        serializer = LoanCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from apps.savings.models import SavingsAccount

        member = Member.objects.filter(pk=serializer.validated_data['member']).first()
        if member is None:
            raise NotFound('Member not found.')
        product = LoanProduct.objects.filter(
            pk=serializer.validated_data['product'], status='active'
        ).first()
        if product is None:
            raise NotFound('Loan product not found.')
        savings = SavingsAccount.objects.filter(
            pk=serializer.validated_data['savings_account'], member=member
        ).first()
        if savings is None:
            raise NotFound('Savings account not found for the member.')
        try:
            loan = services.create_loan(
                member=member,
                product=product,
                savings_account=savings,
                principal=serializer.validated_data['principal'],
                requested_by=request.user,
            )
        except (ValueError, AttributeError) as exc:
            raise ValidationError(str(exc)) from exc
        return Response(LoanSerializer(loan).data, status=http_status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        loan = self.get_object()
        try:
            services.approve(loan, requested_by=request.user)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(LoanSerializer(loan).data)

    @action(detail=True, methods=['post'])
    def disburse(self, request, pk=None):
        loan = self.get_object()
        serializer = LoanActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            tx = services.disburse(
                loan=loan,
                requested_by=request.user,
                idempotency_key=serializer.validated_data.get('idempotency_key'),
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(
            {'loan': LoanSerializer(loan).data, 'transaction': tx.reference},
            status=http_status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'])
    def repay(self, request, pk=None):
        loan = self.get_object()
        serializer = LoanRepaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            tx = services.repay(
                loan=loan,
                amount=serializer.validated_data['amount'],
                requested_by=request.user,
                idempotency_key=serializer.validated_data.get('idempotency_key'),
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(
            {'loan': LoanSerializer(loan).data, 'transaction': tx.reference},
            status=http_status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        loan = self.get_object()
        serializer = LoanActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            services.cancel(
                loan, requested_by=request.user, reason=serializer.validated_data.get('reason', '')
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(LoanSerializer(loan).data)
