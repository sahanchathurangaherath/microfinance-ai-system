from django.urls import path
from .views import (
    RepaymentScheduleView, PostPaymentView,
    PaymentReceiptView, LoanBalanceView, TriggerA4ScanView,
    AllInstallmentsListView
)

urlpatterns = [
    path('', AllInstallmentsListView.as_view()),
    path('loans/<int:loan_id>/schedule/', RepaymentScheduleView.as_view()),
    path('loans/<int:loan_id>/balance/', LoanBalanceView.as_view()),
    path('payments/', PostPaymentView.as_view()),
    path('payments/<int:payment_id>/receipt/', PaymentReceiptView.as_view()),
    path('a4/scan/', TriggerA4ScanView.as_view()),
]