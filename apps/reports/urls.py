from django.urls import path

from . import views

urlpatterns = [
    path('reports/trial-balance/', views.TrialBalanceReport.as_view(), name='report-trial-balance'),
    path('reports/cash-position/', views.CashPositionReport.as_view(), name='report-cash-position'),
    path(
        'reports/member-savings/', views.MemberSavingsReport.as_view(), name='report-member-savings'
    ),
    path('reports/loan-book/', views.LoanBookReport.as_view(), name='report-loan-book'),
]
