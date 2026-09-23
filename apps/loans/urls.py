from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import LoanProductViewSet, LoanViewSet

router = DefaultRouter()
router.register(r'loan-products', LoanProductViewSet, basename='loan-product')
router.register(r'loans', LoanViewSet, basename='loan')

urlpatterns = [path('', include(router.urls))]
