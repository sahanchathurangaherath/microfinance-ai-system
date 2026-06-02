from django.db import models
from django.conf import settings
from apps.clients.models import Client
from apps.loans.models import LoanApplication


class FraudAlert(models.Model):
    ALERT_TYPE_CHOICES = [
        ('DUPLICATE_IDENTITY', 'Duplicate Identity Detected'),
        ('APPLICATION_PATTERN', 'Suspicious Application Pattern'),
        ('PAYMENT_ANOMALY', 'Payment Anomaly'),
        ('UNUSUAL_AMOUNT', 'Unusual Loan Amount'),
        ('KYC_ANOMALY', 'KYC Anomaly'),
        ('BEHAVIORAL', 'Suspicious Behavioral Pattern'),
        ('MANUAL', 'Manually Flagged'),
    ]

    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('UNDER_INVESTIGATION', 'Under Investigation'),
        ('CLEARED', 'Cleared — No Fraud'),
        ('CONFIRMED', 'Fraud Confirmed'),
        ('CLOSED', 'Closed'),
    ]

    client = models.ForeignKey(
        Client, on_delete=models.PROTECT, related_name='fraud_alerts',
        null=True, blank=True
    )
    application = models.ForeignKey(
        LoanApplication, on_delete=models.PROTECT, related_name='fraud_alerts',
        null=True, blank=True
    )
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPE_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='OPEN')

    # A5 output
    fraud_risk_score = models.FloatField(default=0.0)   # 0–100
    ai_rationale = models.TextField()
    detected_signals = models.JSONField(default=list)
    ai_confidence = models.FloatField(default=0.0)

    # Detection source
    triggered_by_agent = models.BooleanField(default=True)
    triggered_at = models.DateTimeField(auto_now_add=True)

    # Investigation
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_fraud_alerts'
    )
    investigation_notes = models.TextField(blank=True)

    def __str__(self):
        return f"[{self.severity}] {self.alert_type} - {self.status}"

    class Meta:
        db_table = 'fraud_alerts'
        ordering = ['-triggered_at']


class FraudInvestigation(models.Model):
    """Detailed investigation record maintained by Compliance Officer."""
    alert = models.OneToOneField(
        FraudAlert, on_delete=models.CASCADE, related_name='investigation'
    )
    investigator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    findings = models.TextField(blank=True)
    evidence_collected = models.JSONField(default=list)
    outcome = models.CharField(
        max_length=20,
        choices=[
            ('CLEARED', 'No Fraud Found'),
            ('CONFIRMED', 'Fraud Confirmed'),
            ('INCONCLUSIVE', 'Inconclusive'),
        ],
        blank=True
    )

    class Meta:
        db_table = 'fraud_investigations'


class ComplianceAction(models.Model):
    """Human-authorized action taken after investigation."""
    ACTION_CHOICES = [
        ('CLEAR_CLIENT', 'Clear Client — No Action'),
        ('FLAG_CLIENT', 'Flag Client for Monitoring'),
        ('SUSPEND_APPLICATION', 'Suspend Loan Application'),
        ('FREEZE_ACCOUNT', 'Freeze Client Account'),
        ('REFER_LEGAL', 'Refer to Legal Team'),
        ('REPORT_AUTHORITY', 'Report to Regulatory Authority'),
        ('BLACKLIST_CLIENT', 'Blacklist Client'),
    ]

    alert = models.ForeignKey(
        FraudAlert, on_delete=models.CASCADE, related_name='compliance_actions'
    )
    action_type = models.CharField(max_length=30, choices=ACTION_CHOICES)
    authorized_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='compliance_authorizations'
    )
    reason = models.TextField()
    action_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.alert} → {self.action_type}"

    class Meta:
        db_table = 'compliance_actions'