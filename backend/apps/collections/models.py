from django.db import models
from django.conf import settings
from apps.loans.models import Loan


class DelinquencyCase(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('PROMISE_TO_PAY', 'Promise to Pay Received'),
        ('ESCALATED', 'Escalated'),
        ('RESOLVED', 'Resolved'),
        ('WRITTEN_OFF', 'Written Off'),
        ('LEGAL', 'Referred to Legal'),
    ]

    BUCKET_CHOICES = [
        ('BUCKET_1_7', '1–7 Days Overdue'),
        ('BUCKET_8_30', '8–30 Days Overdue'),
        ('BUCKET_OVER_30', '30+ Days Overdue'),
    ]

    loan = models.OneToOneField(Loan, on_delete=models.PROTECT, related_name='collection_delinquency_case')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    bucket = models.CharField(max_length=20, choices=BUCKET_CHOICES)
    total_overdue_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    days_overdue = models.IntegerField(default=0)
    overdue_installments_count = models.IntegerField(default=0)
    predicted_default_probability = models.FloatField(null=True, blank=True)
    behavioral_pattern_label      = models.CharField(max_length=30, blank=True)
    llm_recommended_action        = models.TextField(blank=True)

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_collection_cases'
    )

    opened_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Case: {self.loan.loan_number} [{self.status}] - {self.bucket}"

    class Meta:
        db_table = 'collection_delinquency_cases'
        ordering = ['-days_overdue']


class CollectionAction(models.Model):
    """Every contact attempt or action taken by a collections officer."""
    ACTION_TYPES = [
        ('PHONE_CALL', 'Phone Call'),
        ('SMS', 'SMS Sent'),
        ('EMAIL', 'Email Sent'),
        ('FIELD_VISIT', 'Field Visit'),
        ('WRITTEN_NOTICE', 'Written Notice Sent'),
        ('GUARANTOR_CONTACT', 'Guarantor Contacted'),
        ('INTERNAL_NOTE', 'Internal Note'),
    ]

    OUTCOME_CHOICES = [
        ('NO_ANSWER', 'No Answer'),
        ('CONTACTED', 'Client Contacted'),
        ('PROMISED_PAYMENT', 'Promised to Pay'),
        ('REFUSED', 'Refused to Pay'),
        ('DISPUTE', 'Payment in Dispute'),
        ('UNREACHABLE', 'Client Unreachable'),
        ('OTHER', 'Other'),
    ]

    case = models.ForeignKey(
        DelinquencyCase, on_delete=models.CASCADE, related_name='actions'
    )
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    outcome = models.CharField(max_length=20, choices=OUTCOME_CHOICES)
    notes = models.TextField()
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    performed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.case.loan.loan_number} | {self.action_type} | {self.outcome}"

    class Meta:
        db_table = 'collection_actions'
        ordering = ['-performed_at']


class PromiseToPay(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('KEPT', 'Promise Kept'),
        ('BROKEN', 'Promise Broken'),
        ('EXTENDED', 'Extended'),
    ]

    case = models.ForeignKey(
        DelinquencyCase, on_delete=models.CASCADE, related_name='promises'
    )
    promised_amount = models.DecimalField(max_digits=12, decimal_places=2)
    promised_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    recorded_at = models.DateTimeField(auto_now_add=True)
    outcome_notes = models.TextField(blank=True)
    fulfilled_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return (
            f"PTP: {self.case.loan.loan_number} | "
            f"LKR {self.promised_amount} by {self.promised_date} [{self.status}]"
        )

    class Meta:
        db_table = 'promises_to_pay'
        ordering = ['-recorded_at']


class EscalationRecord(models.Model):
    REASON_CHOICES = [
        ('30_DAYS_OVERDUE', '30+ Days Overdue'),
        ('BROKEN_PROMISE', 'Repeated Broken Promises'),
        ('UNREACHABLE', 'Client Unreachable'),
        ('DISPUTE', 'Dispute Raised'),
        ('LEGAL_RISK', 'Legal Action Risk'),
        ('FRAUD_SUSPICION', 'Fraud Suspicion'),
    ]

    case = models.ForeignKey(
        DelinquencyCase, on_delete=models.CASCADE, related_name='escalations'
    )
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    escalated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='escalated_cases'
    )
    escalated_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='received_escalations'
    )
    notes = models.TextField()
    escalated_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Escalation: {self.case.loan.loan_number} - {self.reason}"

    class Meta:
        db_table = 'escalation_records'
        ordering = ['-escalated_at']