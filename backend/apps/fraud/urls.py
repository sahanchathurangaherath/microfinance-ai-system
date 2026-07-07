from django.urls import path
from .views import (
    TriggerFraudCheckView, FraudAlertListView, FraudAlertDetailView,
    OpenInvestigationView, CloseAlertView
)

urlpatterns = [
    path('check', TriggerFraudCheckView.as_view()),
    path('alerts', FraudAlertListView.as_view()),
    path('alerts/<int:pk>', FraudAlertDetailView.as_view()),
    path('alerts/<int:alert_id>/investigate', OpenInvestigationView.as_view()),
    path('alerts/<int:alert_id>/close', CloseAlertView.as_view()),
]