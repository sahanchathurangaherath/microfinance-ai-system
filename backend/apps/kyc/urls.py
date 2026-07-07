from django.urls import path
from apps.clients.views import (
    DocumentUploadView, KYCChecklistUpdateView, A1ValidateClientView
)

urlpatterns = [
    # Document management
    path('<int:client_id>/documents', DocumentUploadView.as_view(), name='kyc_documents'),
    
    # KYC checklist
    path('<int:client_id>/checklist', KYCChecklistUpdateView.as_view(), name='kyc_checklist'),
    
    # A1 validation (submit for AI processing)
    path('<int:client_id>/validate', A1ValidateClientView.as_view(), name='kyc_validate'),
]
