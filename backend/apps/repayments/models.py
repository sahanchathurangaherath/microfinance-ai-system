from django.db import models
from django.conf import settings
from apps.loans.models import Loan


class RepaymentSchedule(models.Model):
    loan = models.OneToOneField(Loan, on_delete=models.CASCADE, related_name='schedule')
    total_installments = models.IntegerField()
    installments_paid = models.IntegerField(default=0)
    installments_overdue = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Schedule: {self.loan.loan_number}"

    class Meta:
        db_table = 'repayment_schedules'


class RepaymentInstallment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('PARTIAL', 'Partial Payment'),
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
    outstanding = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    paid_at = models.DateTimeField(null=True, blank=True)
    days_overdue = models.IntegerField(default=0)
    penalty_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.outstanding:
            self.outstanding = self.amount_due - self.amount_paid
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.schedule.loan.loan_number} | #{self.installment_number} | {self.status}"

    class Meta:
        db_table = 'repayment_installments'
        ordering = ['installment_number']


class Payment(models.Model):
    METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('MOBILE_MONEY', 'Mobile Money'),
        ('CHEQUE', 'Cheque'),
    ]

    loan = models.ForeignKey(Loan, on_delete=models.PROTECT, related_name='payments')
    installment = models.ForeignKey(
        RepaymentInstallment, on_delete=models.PROTECT, related_name='payments'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='CASH')
    reference_number = models.CharField(max_length=100, blank=True)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='received_payments'
    )
    payment_date = models.DateField()
    recorded_at = models.DateTimeField(auto_now_add=True)
    is_penalty_payment = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Payment: {self.loan.loan_number} | {self.amount} on {self.payment_date}"

    class Meta:
        db_table = 'payments'
        ordering = ['-recorded_at']


class PaymentReceipt(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='receipt')
    receipt_number = models.CharField(max_length=20, unique=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    content = models.JSONField(default=dict)

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            last = PaymentReceipt.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.receipt_number = f"RCP{str(next_id).zfill(8)}"
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'payment_receipts'