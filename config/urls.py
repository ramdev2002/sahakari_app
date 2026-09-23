from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.core.health import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health'),
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='api-schema'), name='api-redoc'),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include('apps.identity.urls')),
    path('api/', include('apps.members.urls')),
    path('api/', include('apps.organization.urls')),
    path('api/', include('apps.accounts.urls')),
    path('api/', include('apps.ledger.urls')),
    path('api/', include('apps.transactions.urls')),
    path('api/', include('apps.savings.urls')),
    path('api/', include('apps.audit.urls')),
    path('api/', include('apps.loans.urls')),
    path('api/', include('apps.approvals.urls')),
    path('api/', include('apps.notifications.urls')),
    path('api/', include('apps.reports.urls')),
]

if settings.DEBUG and settings.MEDIA_URL:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
