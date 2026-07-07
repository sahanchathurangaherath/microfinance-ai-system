from django.urls import path
from .views import (
    AuditLogListView, AgentActionLogListView,
    HumanDecisionLogListView, LoginAttemptListView, MyAuditTrailView,
    AIHealthCheckView, EnableManualModeView, DisableManualModeView,
    SystemIncidentListView, ResolveIncidentView,
    ManualReviewQueueView, SubmitManualReviewView, RetryAIRequestView,
    AgentConfigListView, AgentConfigUpdateView, AgentPerformanceView,
    AgentConfigChangeLogListView
)

urlpatterns = [
    # Original audit endpoints
    path('logs', AuditLogListView.as_view()),
    path('agent-actions', AgentActionLogListView.as_view()),
    path('decisions', HumanDecisionLogListView.as_view()),
    path('login-attempts', LoginAttemptListView.as_view()),
    path('my-trail', MyAuditTrailView.as_view()),
    
    # New AI service health and failure handling endpoints
    path('ai/health', AIHealthCheckView.as_view()),
    path('system/manual-mode/enable', EnableManualModeView.as_view()),
    path('system/manual-mode/disable', DisableManualModeView.as_view()),
    path('system/incidents', SystemIncidentListView.as_view()),
    path('system/incidents/<int:incident_id>/resolve', ResolveIncidentView.as_view()),
    path('system/manual-review', ManualReviewQueueView.as_view()),
    path('system/manual-review/<int:case_id>/submit', SubmitManualReviewView.as_view()),
    path('system/manual-review/<int:case_id>/retry', RetryAIRequestView.as_view()),

    # Live Agent Configuration endpoints
    path('agent-config', AgentConfigListView.as_view()),
    path('agent-config/<str:agent_id>', AgentConfigUpdateView.as_view()),
    path('agent-performance/<str:agent_id>', AgentPerformanceView.as_view()),
    path('agent-config-logs', AgentConfigChangeLogListView.as_view()),
]