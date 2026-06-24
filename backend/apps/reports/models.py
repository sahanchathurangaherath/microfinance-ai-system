from django.db import models


class ReportSnapshot(models.Model):
    """
    Stores a point-in-time snapshot of key metrics.
    Generated daily by a scheduled task or on-demand.
    """
    REPORT_TYPES = [
        ('PORTFOLIO', 'Portfolio Summary'),
        ('DEFAULT_RATE', 'Default Rate'),
        ('ARREARS', 'Arrears Distribution'),
        ('DISBURSEMENT', 'Disbursement Summary'),
        ('RISK_DISTRIBUTION', 'Risk Score Distribution'),
        ('AGENT_PERFORMANCE', 'AI Agent Performance'),
        ('FRAUD', 'Fraud Alert Summary'),
    ]

    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    data = models.JSONField(default=dict)
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.CharField(max_length=50, default='system')
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.report_type} — {self.generated_at.date()}"

    class Meta:
        db_table = 'report_snapshots'
        ordering = ['-generated_at']


class KPIRecord(models.Model):
    """Tracks key performance indicators over time."""
    KPI_NAMES = [
        ('approval_time_hours', 'Avg Loan Approval Time (hrs)'),
        ('default_rate_percent', 'Default Rate (%)'),
        ('repayment_success_rate', 'Repayment Success Rate (%)'),
        ('ai_acceptance_rate', 'AI Recommendation Acceptance Rate (%)'),
        ('fraud_detection_rate', 'Fraud Detection Rate (%)'),
        ('disbursement_count', 'Disbursements This Month'),
        ('active_loan_count', 'Active Loans'),
        ('overdue_loan_count', 'Loans with Overdue Installments'),
    ]

    kpi_name = models.CharField(max_length=50)
    value = models.FloatField()
    recorded_at = models.DateTimeField(auto_now_add=True)
    period = models.CharField(max_length=20, blank=True)  # e.g. "2025-01"

    class Meta:
        db_table = 'kpi_records'
        ordering = ['-recorded_at']