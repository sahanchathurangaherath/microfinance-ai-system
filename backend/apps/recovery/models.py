from django.db import models
from django.conf import settings


class DelinquencyCase(models.Model):
    """
    Tracks delinquent loans and AI-recommended recovery actions.
    Created when a loan becomes delinquent and monitored by Collections Officer.
    """
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('RESOLVED', 'Resolved'),
        ('ESCALATED', 'Escalated'),
        ('WRITTEN_OFF', 'Written Off'),
    ]

    # Link to loan
    loan = models.OneToOneField(
        'loans.Loan', on_delete=models.CASCADE, related_name='delinquency_case'
    )

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    days_overdue = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    # Officer assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_cases'
    )

    # AI-generated insights (Step 9.4 fields)
    predicted_default_probability = models.FloatField(null=True, blank=True)
    behavioral_pattern_label = models.CharField(max_length=30, blank=True)
    llm_recommended_action = models.TextField(blank=True)

    # Officer's action and notes
    action_taken = models.TextField(blank=True)
    officer_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Delinquency: {self.loan.loan_number} - {self.days_overdue} days overdue"

    class Meta:
        db_table = 'delinquency_cases'
        ordering = ['-created_at']
