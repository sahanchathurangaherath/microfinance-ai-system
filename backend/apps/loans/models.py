from django.db import models
from django.conf import settings
from apps.clients.models import Client


class LoanProduct(models.Model):
    """Defines available loan types."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    min_amount = models.DecimalField(max_digits=12, decimal_places=2)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2)
    min_duration_months = models.IntegerField()
    max_duration_months = models.IntegerField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)  # Annual %
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'loan_products'


class LoanApplication(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('AI_SCREENING', 'AI Screening'),
        ('RISK_REVIEWED', 'Risk Reviewed'),
        ('MANAGER_REVIEW', 'Manager Review'),
        ('COMMITTEE_REVIEW', 'Committee Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('MORE_INFO_REQUIRED', 'More Information Required'),
        ('CANCELLED', 'Cancelled'),
    ]

    LOAN_PURPOSE_CHOICES = [
        ('BUSINESS_EXPANSION', 'Business Expansion'),
        ('WORKING_CAPITAL', 'Working Capital'),
        ('EQUIPMENT_PURCHASE', 'Equipment Purchase'),
        ('AGRICULTURE', 'Agriculture'),
        ('EDUCATION', 'Education'),
        ('MEDICAL', 'Medical Emergency'),
        ('HOME_IMPROVEMENT', 'Home Improvement'),
        ('DEBT_CONSOLIDATION', 'Debt Consolidation'),
        ('OTHER', 'Other'),
    ]

    # Application identity
    application_number = models.CharField(max_length=20, unique=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='loan_applications')
    loan_product = models.ForeignKey(
        LoanProduct, on_delete=models.SET_NULL, null=True, blank=True
    )

    # Loan request details
    requested_amount = models.DecimalField(max_digits=12, decimal_places=2)
    requested_duration_months = models.IntegerField()
    loan_purpose = models.CharField(max_length=50, choices=LOAN_PURPOSE_CHOICES)
    purpose_description = models.TextField(blank=True)

    # Status
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='DRAFT')

    # Who created it
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_applications'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    # Notes
    officer_notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.application_number:
            last = LoanApplication.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.application_number = f"LA{str(next_id).zfill(7)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.application_number} - {self.client} [{self.status}]"

    class Meta:
        db_table = 'loan_applications'
        ordering = ['-created_at']


class CashflowAssessment(models.Model):
    """Financial details entered by loan officer for this application."""
    application = models.OneToOneField(
        LoanApplication, on_delete=models.CASCADE, related_name='cashflow'
    )
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2)
    other_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    monthly_expenses = models.DecimalField(max_digits=12, decimal_places=2)
    existing_loan_payments = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    proposed_monthly_payment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_cashflow = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    debt_to_income_ratio = models.FloatField(null=True, blank=True)
    officer_assessment_notes = models.TextField(blank=True)

    def calculate_ratios(self):
        total_income = float(self.monthly_income) + float(self.other_income)
        total_debt = float(self.existing_loan_payments) + float(self.proposed_monthly_payment)
        if total_income > 0:
            self.debt_to_income_ratio = round(total_debt / total_income, 4)
        self.net_cashflow = total_income - float(self.monthly_expenses) - total_debt
        return self

    class Meta:
        db_table = 'cashflow_assessments'


class LoanDocument(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ('BUSINESS_PLAN', 'Business Plan'),
        ('QUOTATION', 'Quotation / Pro Forma Invoice'),
        ('COLLATERAL_PHOTO', 'Collateral Photo'),
        ('COLLATERAL_VALUATION', 'Collateral Valuation Report'),
        ('BANK_STATEMENT', 'Bank Statement'),
        ('TAX_RETURN', 'Tax Return'),
        ('OTHER', 'Other'),
    ]

    application = models.ForeignKey(
        LoanApplication, on_delete=models.CASCADE, related_name='documents'
    )
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES)
    file = models.FileField(upload_to='loan_documents/%Y/%m/')
    file_name = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.application.application_number} - {self.document_type}"

    class Meta:
        db_table = 'loan_documents'


class ApplicationStatusHistory(models.Model):
    """Full audit trail of every status change on a loan application."""
    application = models.ForeignKey(
        LoanApplication, on_delete=models.CASCADE, related_name='status_history'
    )
    from_status = models.CharField(max_length=30, blank=True)
    to_status = models.CharField(max_length=30)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    changed_by_role = models.CharField(max_length=50, blank=True)
    reason = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.application.application_number}: {self.from_status} → {self.to_status}"

    class Meta:
        db_table = 'application_status_history'
        ordering = ['timestamp']