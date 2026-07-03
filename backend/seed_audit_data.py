import os
import sys
sys.path.append('c:/Users/Sahan/Documents/Agents development/MicroFinance-AgenticAi/microfinance-ai-system/backend')

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.audit.models import SystemIncident, ManualReviewCase, AgentConfigChangeLog
from django.utils import timezone

User = get_user_model()
admin_user = User.objects.filter(role='admin').first()
compliance_user = User.objects.filter(role='compliance_officer').first()
risk_user = User.objects.filter(role='risk_analyst').first()

if not admin_user:
    admin_user = User.objects.create_superuser(username='admin_seed', email='admin_seed@test.com', password='password', role='admin')

# Clear existing to prevent duplicates
SystemIncident.objects.all().delete()
ManualReviewCase.objects.all().delete()
AgentConfigChangeLog.objects.all().delete()

# 1. Seed System Incidents
# Open incident
incident_1 = SystemIncident.objects.create(
    incident_type="A2_RISK_ASSESSMENT_TIMEOUT",
    severity="PARTIAL",
    status="OPEN",
    agent_id="A2",
    affected_reference="LoanApplication#1042",
    error_message="FastAPI read timeout of 10.0s reached during credit scoring calculation.",
    occurred_at=timezone.now() - timezone.timedelta(hours=2)
)

# Resolved incident
incident_2 = SystemIncident.objects.create(
    incident_type="A5_FRAUD_SERVICE_OFFLINE",
    severity="HARD",
    status="RESOLVED",
    agent_id="A5",
    affected_reference="Client#829",
    error_message="FastAPI server on port 8001 connection refused. Service process crashed.",
    occurred_at=timezone.now() - timezone.timedelta(days=1),
    resolved_at=timezone.now() - timezone.timedelta(hours=20),
    resolved_by=admin_user,
    resolution_notes="Restarted FastAPI docker container service. Health checks are passing."
)

# Acknowledged incident
incident_3 = SystemIncident.objects.create(
    incident_type="A3_RECOMMENDATION_LOW_CONF",
    severity="SOFT",
    status="ACKNOWLEDGED",
    agent_id="A3",
    affected_reference="LoanApplication#1039",
    error_message="LLM response confidence score 0.58 fell below policy threshold of 0.65.",
    occurred_at=timezone.now() - timezone.timedelta(hours=10)
)

# 2. Seed Manual Review Cases
# Pending
ManualReviewCase.objects.create(
    incident=incident_1,
    agent_id="A2",
    reference_model="LoanApplication",
    reference_id=1042,
    status="PENDING",
    manual_notes="AI scoring service timed out. Manually verify bank statement income and compute credit risk score."
)

# Completed review
ManualReviewCase.objects.create(
    incident=incident_3,
    agent_id="A3",
    reference_model="LoanApplication",
    reference_id=1039,
    status="COMPLETED",
    assigned_to=risk_user or admin_user,
    manual_score=75.0,
    manual_decision="APPROVED",
    manual_notes="Reviewed client history and income consistency. Approved manually despite low AI confidence.",
    completed_at=timezone.now() - timezone.timedelta(hours=5)
)

# In Progress review
ManualReviewCase.objects.create(
    incident=incident_2,
    agent_id="A5",
    reference_model="ClientOnboarding",
    reference_id=829,
    status="IN_PROGRESS",
    assigned_to=compliance_user or admin_user,
    manual_notes="Investigating duplicate NIC matching during service downtime. Checking system records."
)

# 3. Seed Config Change Logs
AgentConfigChangeLog.objects.create(
    agent_id="A2",
    field_changed="confidence_threshold",
    old_value="0.65",
    new_value="0.75",
    changed_by=admin_user,
    reason="Scale up safety checks for agricultural season loans.",
    changed_at=timezone.now() - timezone.timedelta(hours=12)
)

AgentConfigChangeLog.objects.create(
    agent_id="A5",
    field_changed="llm_enabled",
    old_value="True",
    new_value="False",
    changed_by=compliance_user or admin_user,
    reason="Temporarily disabling LLM mode due to false positive NIC matching spike.",
    changed_at=timezone.now() - timezone.timedelta(hours=18)
)

AgentConfigChangeLog.objects.create(
    agent_id="A6",
    field_changed="daily_token_budget",
    old_value="Unlimited",
    new_value="500000",
    changed_by=admin_user,
    reason="Capping token limits for Sinhala/Tamil SMS marketing drafts campaign.",
    changed_at=timezone.now() - timezone.timedelta(days=2)
)

print("Successfully seeded Audit logs, System Incidents, and Manual Review Cases!")
