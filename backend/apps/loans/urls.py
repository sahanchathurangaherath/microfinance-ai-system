from django.urls import path
from .views import (
    LoanApplicationListCreateView, LoanApplicationDetailView,
    SubmitApplicationView, ApplicationStatusView,
    CashflowCreateView, LoanDocumentUploadView, LoanProductListView,
    TriggerRiskAssessmentView, RiskAnalystReviewView, RiskHistoryView,
    TriggerRecommendationView, GetRecommendationView, OfficerFeedbackView,
    ReadyForDisbursementView, VerifyDisbursementConditionsView,
    ProcessDisbursementView, DisbursementReceiptView

)

urlpatterns = [
    path('products/', LoanProductListView.as_view(), name='loan_products'),
    path('applications/', LoanApplicationListCreateView.as_view(), name='application_list_create'),
    path('applications/<int:pk>/', LoanApplicationDetailView.as_view(), name='application_detail'),
    path('applications/<int:pk>/submit/', SubmitApplicationView.as_view(), name='application_submit'),
    path('applications/<int:pk>/status/', ApplicationStatusView.as_view(), name='application_status'),
    path('applications/<int:pk>/cashflow/', CashflowCreateView.as_view(), name='cashflow_create'),
    path('applications/<int:pk>/documents/', LoanDocumentUploadView.as_view(), name='loan_doc_upload'),
     path('applications/<int:pk>/risk-assess/', TriggerRiskAssessmentView.as_view()),
    path('applications/<int:pk>/risk-review/', RiskAnalystReviewView.as_view()),
    path('risk/history/<int:client_id>/', RiskHistoryView.as_view()),
    path('applications/<int:pk>/recommend/', TriggerRecommendationView.as_view()),
    path('applications/<int:pk>/recommendation/', GetRecommendationView.as_view()),
    path('applications/<int:pk>/recommendation/feedback/', OfficerFeedbackView.as_view()),
    path('disbursements/ready/', ReadyForDisbursementView.as_view()),
    path('disbursements/<int:pk>/conditions/', VerifyDisbursementConditionsView.as_view()),
    path('disbursements/<int:pk>/process/', ProcessDisbursementView.as_view()),
    path('disbursements/<int:pk>/receipt/', DisbursementReceiptView.as_view()),
]