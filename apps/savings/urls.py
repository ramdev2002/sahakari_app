from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import SavingsAccountViewSet, SavingsProductViewSet

router = DefaultRouter()
router.register(r'savings-products', SavingsProductViewSet, basename='savings-product')
router.register(r'savings-accounts', SavingsAccountViewSet, basename='savings-account')

urlpatterns = [path('', include(router.urls))]
