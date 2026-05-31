from django.db import models
from apps.loans.models import Loan


class RepaymentSchedule(models.Model):
    loan = models.OneToOneField(Loan, on_delete=models.CASCADE, related_name='schedule')
    total_installments = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Schedule for {self.loan.loan_number}"

    class Meta:
        db_table = 'repayment_schedules'


class RepaymentInstallment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('PARTIAL', 'Partial'),
        ('OVERDUE', 'Overdue'),
        ('WAIVED', 'Waived'),
    ]

    schedule = models.ForeignKey(
        RepaymentSchedule, on_delete=models.CASCADE, related_name='installments'
    )
    installment_number = models.IntegerField()
    due_date = models.DateField()
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    principal_component = models.DecimalField(max_digits=12, decimal_places=2)
    interest_component = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    paid_at = models.DateTimeField(null=True, blank=True)
    penalty_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.schedule.loan.loan_number} - Inst #{self.installment_number} [{self.status}]"

    class Meta:
        db_table = 'repayment_installments'
        ordering = ['installment_number']