from rest_framework import status as http_status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from apps.identity.permissions import IsSuperUserOrAdministrativeOfficer
from apps.members.models import Member

from . import services
from .models import SavingsAccount, SavingsProduct
from .serializers import (
    SavingsAccountCreateSerializer,
    SavingsAccountSerializer,
    SavingsProductSerializer,
)


class SavingsProductViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SavingsProductSerializer

    def get_queryset(self):
        return SavingsProduct.objects.filter(status='active').order_by('code')

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsSuperUserOrAdministrativeOfficer()]
        return [IsAuthenticated()]

    def perform_destroy(self, instance):
        instance.soft_delete()


class SavingsAccountViewSet(GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SavingsAccountSerializer

    def get_queryset(self):
        queryset = SavingsAccount.objects.select_related(
            'member', 'product', 'account', 'account__balance', 'branch'
        ).filter(status='active')
        member = self.request.query_params.get('member')
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
    def open(self, request):
        serializer = SavingsAccountCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = Member.objects.filter(pk=serializer.validated_data['member']).first()
        if member is None:
            raise NotFound('Member not found.')
        product = SavingsProduct.objects.filter(
            pk=serializer.validated_data['product'], status='active'
        ).first()
        if product is None:
            raise NotFound('Savings product not found.')
        try:
            savings, opening_tx = services.open_savings_account(
                member=member,
                product=product,
                branch=getattr(request.user, 'branch', None),
                initial_deposit=serializer.validated_data.get('initial_deposit', 0),
                requested_by=request.user,
                idempotency_key=serializer.validated_data.get('idempotency_key'),
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        response = {
            'savings_account': SavingsAccountSerializer(savings).data,
            'opening_transaction': (opening_tx.reference if opening_tx else None),
        }
        return Response(response, status=http_status.HTTP_201_CREATED)
