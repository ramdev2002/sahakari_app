from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AccountBalanceViewSet, AccountTypeViewSet, AccountViewSet

router = DefaultRouter()
router.register(r'account-types', AccountTypeViewSet, basename='account-type')
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'account-balances', AccountBalanceViewSet, basename='account-balance')

urlpatterns = [path('', include(router.urls))]
