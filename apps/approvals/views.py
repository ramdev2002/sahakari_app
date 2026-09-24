from rest_framework import status as http_status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from apps.core.permissions import CanDecideApprovals, CanManageApprovals, CanViewApprovals

from . import services
from .models import ApprovalRequest, ApprovalRule
from .serializers import (
    ApprovalCreateSerializer,
    ApprovalDecisionSerializer,
    ApprovalRequestSerializer,
    ApprovalRuleSerializer,
)


class ApprovalRequestViewSet(GenericViewSet):
    permission_classes = [IsAuthenticated, CanViewApprovals]
    serializer_class = ApprovalRequestSerializer

    def get_queryset(self):
        queryset = ApprovalRequest.objects.select_related('requested_by', 'reviewed_by').order_by(
            '-created_at'
        )
        status = self.request.query_params.get('status')
        entity_type = self.request.query_params.get('entity_type')
        if status:
            queryset = queryset.filter(status=status)
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)
        return queryset

    def get_permissions(self):
        if self.action == 'decide':
            return [IsAuthenticated(), CanDecideApprovals()]
        return [IsAuthenticated(), CanViewApprovals()]

    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        return Response(self.get_serializer(self.get_object()).data)

    @action(detail=False, methods=['post'])
    def create_request(self, request):
        serializer = ApprovalCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        approval, created = services.request_approval(
            entity_type=serializer.validated_data['entity_type'],
            entity_id=serializer.validated_data['entity_id'],
            action=serializer.validated_data['action'],
            requested_by=request.user,
            note=serializer.validated_data.get('note', ''),
        )
        status_code = http_status.HTTP_201_CREATED if created else http_status.HTTP_200_OK
        return Response(ApprovalRequestSerializer(approval).data, status=status_code)

    @action(detail=True, methods=['post'])
    def decide(self, request, pk=None):
        approval = self.get_object()
        serializer = ApprovalDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            services.decide(
                approval,
                decision=serializer.validated_data['decision'],
                reviewer=request.user,
                comment=serializer.validated_data.get('comment', ''),
            )
        except PermissionError as exc:
            raise PermissionDenied(str(exc)) from exc
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(ApprovalRequestSerializer(approval).data)


class ApprovalRuleViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, CanManageApprovals]
    serializer_class = ApprovalRuleSerializer

    def get_queryset(self):
        return ApprovalRule.objects.order_by('action')
