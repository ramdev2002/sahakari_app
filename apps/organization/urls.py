from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BranchViewSet, DepartmentViewSet, OrganizationViewSet

router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'branches', BranchViewSet, basename='branch')
router.register(r'departments', DepartmentViewSet, basename='department')

urlpatterns = [path('', include(router.urls))]
