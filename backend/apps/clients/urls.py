from django.urls import path
from .views import (
    ClientListCreateView, ClientDetailView,
    ClientAddressView, ClientBusinessView, ClientIncomeView,
    DocumentUploadView, KYCChecklistUpdateView, A1ValidateClientView
)

urlpatterns = [
    path('', ClientListCreateView.as_view(), name='client_list_create'),
    path('<int:pk>/', ClientDetailView.as_view(), name='client_detail'),
    path('<int:client_id>/address/', ClientAddressView.as_view(), name='client_address'),
    path('<int:client_id>/business/', ClientBusinessView.as_view(), name='client_business'),
    path('<int:client_id>/income/', ClientIncomeView.as_view(), name='client_income'),
    path('<int:client_id>/documents/', DocumentUploadView.as_view(), name='document_upload'),
    path('<int:client_id>/kyc/', KYCChecklistUpdateView.as_view(), name='kyc_checklist'),
    path('<int:client_id>/kyc/submit/', A1ValidateClientView.as_view(), name='a1_validate'),
]