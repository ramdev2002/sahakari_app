from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.identity.permissions import IsStaffUser

from . import services

_RESPONSES = {
    200: OpenApiResponse(
        inline_serializer(
            'ReportResponse',
            fields={
                'result': serializers.DictField(default=dict, help_text='Aggregated report data')
            },
        ),
        description='Aggregated report data',
    )
}


class ReportBaseView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]


@extend_schema(responses=_RESPONSES)
class TrialBalanceReport(ReportBaseView):
    def get(self, request):
        return Response(services.trial_balance())


@extend_schema(responses=_RESPONSES)
class CashPositionReport(ReportBaseView):
    def get(self, request):
        return Response(services.cash_position())


@extend_schema(responses=_RESPONSES)
class MemberSavingsReport(ReportBaseView):
    def get(self, request):
        member_id = request.query_params.get('member')
        return Response({'rows': services.member_savings_balances(member_id)})


@extend_schema(responses=_RESPONSES)
class LoanBookReport(ReportBaseView):
    def get(self, request):
        product_code = request.query_params.get('product')
        return Response(services.loan_book(product_code))
