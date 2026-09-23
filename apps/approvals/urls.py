from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ApprovalRequestViewSet, ApprovalRuleViewSet

router = DefaultRouter()
router.register(r'approvals', ApprovalRequestViewSet, basename='approval')
router.register(r'approval-rules', ApprovalRuleViewSet, basename='approval-rule')

urlpatterns = [path('', include(router.urls))]
