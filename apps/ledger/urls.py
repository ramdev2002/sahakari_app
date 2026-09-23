from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import JournalViewSet, LedgerEntryViewSet

router = DefaultRouter()
router.register(r'journals', JournalViewSet, basename='journal')
router.register(r'ledger-entries', LedgerEntryViewSet, basename='ledger-entry')

urlpatterns = [path('', include(router.urls))]
