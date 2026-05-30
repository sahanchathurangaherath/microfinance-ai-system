from django.urls import path
from .views import (
    PendingRiskReviewView, PendingManagerReviewView, PendingCommitteeView,
    AllPendingView, RiskAnalystDecisionView, BranchManagerDecisionView,
    CommitteeVoteView, ApprovalHistoryView
)

urlpatterns = [
    path('pending/', AllPendingView.as_view()),
    path('pending/risk-review/', PendingRiskReviewView.as_view()),
    path('pending/manager-review/', PendingManagerReviewView.as_view()),
    path('pending/committee/', PendingCommitteeView.as_view()),
    path('<int:loan_id>/risk-decision/', RiskAnalystDecisionView.as_view()),
    path('<int:loan_id>/manager-decision/', BranchManagerDecisionView.as_view()),
    path('<int:loan_id>/committee-vote/', CommitteeVoteView.as_view()),
    path('<int:loan_id>/history/', ApprovalHistoryView.as_view()),
]