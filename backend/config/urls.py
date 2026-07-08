
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include, re_path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny

schema_view = get_schema_view(
    openapi.Info(
        title="Microfinance AI System API",
        default_version='v1',
        description="API documentation for Microfinance Management AI System",
    ),
    public=True,
    permission_classes=[AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r'^api/auth/?', include('apps.users.urls')),
    re_path(r'^api/users/?', include('apps.users.urls_users')),
    re_path(r'^api/clients/?', include('apps.clients.urls')),
    re_path(r'^api/kyc/?', include('apps.kyc.urls')),
    re_path(r'^api/loans/?', include('apps.loans.urls')),
    re_path(r'^api/docs/?', schema_view.with_ui('swagger', cache_timeout=0)),
    re_path(r'^api/redoc/?', schema_view.with_ui('redoc', cache_timeout=0)),
    re_path(r'^api/approvals/?', include('apps.approvals.urls')),
    re_path(r'^api/repayments/?', include('apps.repayments.urls')),
    re_path(r'^api/collections/?', include('apps.collections.urls')),
    re_path(r'^api/fraud/?', include('apps.fraud.urls')),
    re_path(r'^api/notifications/?', include('apps.notifications.urls')),
    re_path(r'^api/reports/?', include('apps.reports.urls')),
    re_path(r'^api/audit/?', include('apps.audit.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)