
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
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
    path('api/auth/', include('apps.users.urls')),
    path('api/users/', include('apps.users.urls_users')),
    path('api/clients/', include('apps.clients.urls')),
    path('api/loans/', include('apps.loans.urls')),
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0)),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0)),
    path('api/approvals/', include('apps.approvals.urls')),
    path('api/', include('apps.repayments.urls')),  
    path('api/collections/', include('apps.collections.urls')),

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)