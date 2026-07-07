from django.urls import path
from .views import (
    CreateCasesFromA4View, OverdueCaseListView, AssignCaseView,
    LogContactAttemptView, RecordPromiseToPayView, UpdatePromiseStatusView,
    EscalateCaseView, CaseHistoryView, ResolveCaseView
)

urlpatterns = [
    path('create-from-scan', CreateCasesFromA4View.as_view()),
    path('overdue', OverdueCaseListView.as_view()),
    path('<int:case_id>/assign', AssignCaseView.as_view()),
    path('<int:case_id>/contact', LogContactAttemptView.as_view()),
    path('<int:case_id>/promise-to-pay', RecordPromiseToPayView.as_view()),
    path('<int:case_id>/escalate', EscalateCaseView.as_view()),
    path('<int:case_id>/history', CaseHistoryView.as_view()),
    path('<int:case_id>/resolve', ResolveCaseView.as_view()),
    path('promises/<int:ptp_id>/update', UpdatePromiseStatusView.as_view()),
]