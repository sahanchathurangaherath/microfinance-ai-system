from django.db import models
from django.conf import settings
from apps.loans.models import LoanApplication


class ApprovalWorkflow(models.Model):
    """
    Master record tracking the full approval lifecycle of a loan application.
    Created automatically when an application enters RISK_REVIEWED.
    """
    STATUS_CHOICES = [
        ('PENDING_RISK_REVIEW', 'Pending Risk Analyst Review'),
        ('PENDING_MANAGER_REVIEW', 'Pending Branch Manager Review'),
        ('PENDING_COMMITTEE', 'Pending Credit Committee'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('MORE_INFO_REQUIRED', 'More Information Required'),
    ]

    application = models.OneToOneField(
        LoanApplication, on_delete=models.CASCADE, related_name='approval_workflow'
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING_RISK_REVIEW')
    requires_committee = models.BooleanField(default=False)
    committee_threshold = models.DecimalField(
        max_digits=12, decimal_places=2, default=500000
    )  # Amount above which committee review is required
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Workflow: {self.application.application_number} [{self.status}]"

    class Meta:
        db_table = 'approval_workflows'


class ApprovalDecision(models.Model):
    """Individual decision made at each step of the approval chain."""
    STEP_CHOICES = [
        ('RISK_ANALYST', 'Risk Analyst Review'),
        ('BRANCH_MANAGER', 'Branch Manager Review'),
        ('CREDIT_COMMITTEE', 'Credit Committee Decision'),
    ]

    DECISION_CHOICES = [
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('MORE_INFO', 'More Information Required'),
        ('ESCALATE', 'Escalate to Next Level'),
    ]

    workflow = models.ForeignKey(
        ApprovalWorkflow, on_delete=models.CASCADE, related_name='decisions'
    )
    step = models.CharField(max_length=30, choices=STEP_CHOICES)
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='approval_decisions'
    )
    comments = models.TextField()
    ai_recommendation_followed = models.BooleanField(null=True, blank=True)
    override_reason = models.TextField(blank=True)
    decided_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.workflow.application.application_number} - {self.step}: {self.decision}"

    class Meta:
        db_table = 'approval_decisions'
        ordering = ['decided_at']


class CommitteeDecision(models.Model):
    """Used when 2+ committee members vote."""
    workflow = models.OneToOneField(
        ApprovalWorkflow, on_delete=models.CASCADE, related_name='committee_decision'
    )
    final_decision = models.CharField(
        max_length=20,
        choices=[('APPROVED', 'Approved'), ('REJECTED', 'Rejected')],
        blank=True
    )
    vote_for = models.IntegerField(default=0)
    vote_against = models.IntegerField(default=0)
    quorum_reached = models.BooleanField(default=False)
    meeting_notes = models.TextField(blank=True)
    finalized_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'committee_decisions'