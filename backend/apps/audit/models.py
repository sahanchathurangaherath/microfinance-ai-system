from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    """
    Universal audit trail. One entry per significant action.
    This table must never be deletable by normal users.
    """
    ACTION_TYPES = [
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('FAILED_LOGIN', 'Failed Login'),
        ('CREATE', 'Create Record'),
        ('UPDATE', 'Update Record'),
        ('DELETE', 'Delete / Deactivate'),
        ('STATUS_CHANGE', 'Status Change'),
        ('APPROVAL', 'Approval Decision'),
        ('DISBURSEMENT', 'Loan Disbursement'),
        ('PAYMENT', 'Payment Posted'),
        ('AI_ACTION', 'AI Agent Action'),
        ('OVERRIDE', 'AI Override by Human'),
        ('ESCALATION', 'Case Escalation'),
        ('FRAUD_ACTION', 'Fraud / Compliance Action'),
        ('PERMISSION_CHANGE', 'Permission / Role Change'),
        ('EXPORT', 'Data Export'),
        ('SYSTEM', 'System Event'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='audit_entries'
    )
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=50, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    # Before/after state (optional — for status changes)
    status_before = models.CharField(max_length=50, blank=True)
    status_after = models.CharField(max_length=50, blank=True)

    # Structured extra data
    extra_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"[{self.action_type}] {self.model_name} #{self.object_id} by {self.user} at {self.timestamp}"

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']


class AgentActionLog(models.Model):
    """
    Records every AI agent invocation with full input/output traceability.
    This is the evidence trail that proves AI was only advisory.
    """
    AGENT_IDS = [
        ('A1', 'Data Collection Agent'),
        ('A2', 'Risk Assessment Agent'),
        ('A3', 'Recommendation Agent'),
        ('A4', 'Monitoring Agent'),
        ('A5', 'Fraud Detection Agent'),
        ('A6', 'Communication Agent'),
    ]

    agent_id = models.CharField(max_length=5, choices=AGENT_IDS)
    agent_name = models.CharField(max_length=50)

    # What triggered the agent
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    trigger_type = models.CharField(max_length=50, blank=True)  # 'manual', 'automatic'

    # Input/output
    input_reference = models.CharField(max_length=100, blank=True)
    input_hash = models.CharField(max_length=64, blank=True)  # SHA256 hash of input
    input_payload = models.JSONField(default=dict)
    output_payload = models.JSONField(default=dict)

    # AI quality metrics
    confidence = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=30, blank=True)  # SUCCESS, LOW_CONFIDENCE, etc.
    rationale = models.TextField(blank=True)

    # Time
    invoked_at = models.DateTimeField(auto_now_add=True)
    response_time_ms = models.IntegerField(null=True, blank=True)

    # LLM metadata (for local or cloud LLM calls)
    llm_model_used = models.CharField(max_length=50, blank=True)
    prompt_tokens_used = models.IntegerField(default=0)
    completion_tokens_used = models.IntegerField(default=0)
    llm_raw_response = models.TextField(blank=True)
    hallucination_check_passed = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.agent_id} | {self.input_reference} | {self.status} at {self.invoked_at}"

    class Meta:
        db_table = 'agent_action_logs'
        ordering = ['-invoked_at']


class HumanDecisionLog(models.Model):
    """
    Every approval, rejection, or override made by a human officer.
    Captures whether they followed the AI recommendation.
    """
    DECISION_TYPES = [
        ('LOAN_APPROVAL', 'Loan Approval'),
        ('LOAN_REJECTION', 'Loan Rejection'),
        ('AI_OVERRIDE', 'AI Recommendation Override'),
        ('ESCALATION_APPROVE', 'Escalation Approved'),
        ('COMMITTEE_VOTE', 'Committee Vote'),
        ('DISBURSEMENT_AUTH', 'Disbursement Authorization'),
        ('FRAUD_DECISION', 'Fraud Investigation Decision'),
        ('COMPLIANCE_ACTION', 'Compliance Action'),
    ]

    officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='human_decisions'
    )
    officer_role = models.CharField(max_length=50, blank=True)
    decision_type = models.CharField(max_length=30, choices=DECISION_TYPES)
    reference_model = models.CharField(max_length=100, blank=True)
    reference_id = models.CharField(max_length=50, blank=True)
    decision = models.CharField(max_length=50)
    reason = models.TextField()
    ai_recommendation = models.CharField(max_length=50, blank=True)
    followed_ai = models.BooleanField(null=True, blank=True)
    override_justification = models.TextField(blank=True)
    decided_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.officer} | {self.decision_type} | {self.decision} at {self.decided_at}"

    class Meta:
        db_table = 'human_decision_logs'
        ordering = ['-decided_at']


class LoginAttempt(models.Model):
    username_attempted = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    success = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user_agent = models.TextField(blank=True)
    failure_reason = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'login_attempts'
        ordering = ['-timestamp']


class PermissionChangeLog(models.Model):
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='permission_changes_made'
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='permission_changes_received'
    )
    old_role = models.CharField(max_length=50, blank=True)
    new_role = models.CharField(max_length=50)
    reason = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'permission_change_logs'
        ordering = ['-changed_at']


class AIServiceStatus(models.Model):
    """
    Tracks the health of the FastAPI AI service.
    Updated on every health check ping.
    """
    STATUS_CHOICES = [
        ('ONLINE', 'Online'),
        ('DEGRADED', 'Degraded'),
        ('OFFLINE', 'Offline'),
    ]

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ONLINE')
    last_checked = models.DateTimeField(auto_now=True)
    last_online = models.DateTimeField(null=True, blank=True)
    consecutive_failures = models.IntegerField(default=0)
    manual_mode_active = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"AI Service: {self.status} (manual_mode={self.manual_mode_active})"

    class Meta:
        db_table = 'ai_service_status'


class SystemIncident(models.Model):
    """
    Records every AI failure or system error event.
    Never deleted — permanent incident log.
    """
    SEVERITY_CHOICES = [
        ('SOFT', 'Soft Failure — Low Confidence Response'),
        ('HARD', 'Hard Failure — Service Unreachable'),
        ('PARTIAL', 'Partial Failure — Timeout'),
    ]

    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('ACKNOWLEDGED', 'Acknowledged'),
        ('RESOLVED', 'Resolved'),
    ]

    incident_type = models.CharField(max_length=50)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    agent_id = models.CharField(max_length=5, blank=True)
    affected_reference = models.CharField(max_length=100, blank=True)
    error_message = models.TextField(blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    resolution_notes = models.TextField(blank=True)

    def __str__(self):
        return f"[{self.severity}] {self.incident_type} at {self.occurred_at}"

    class Meta:
        db_table = 'system_incidents'
        ordering = ['-occurred_at']


class ManualReviewCase(models.Model):
    """
    Created when an AI agent fails for a specific application or client.
    Staff follow this as the manual processing record.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending Manual Review'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('AI_RETRY_QUEUED', 'AI Retry Queued'),
        ('RESOLVED_BY_AI', 'Resolved by AI After Recovery'),
    ]

    incident = models.ForeignKey(
        SystemIncident, on_delete=models.SET_NULL, null=True, blank=True
    )
    agent_id = models.CharField(max_length=5)
    reference_model = models.CharField(max_length=100)
    reference_id = models.IntegerField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True
    )
    manual_score = models.FloatField(null=True, blank=True)
    manual_decision = models.CharField(max_length=100, blank=True)
    manual_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    retry_after_recovery = models.BooleanField(default=True)

    def __str__(self):
        return f"ManualReview: {self.agent_id} for {self.reference_model}#{self.reference_id}"

    class Meta:
        db_table = 'manual_review_cases'
        ordering = ['-created_at']