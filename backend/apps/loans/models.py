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
        ('RISK_ASSESSED', 'Risk Assessed'),
        ('RISK_REVIEWED', 'Risk Reviewed'),
        ('MANAGER_REVIEW', 'Manager Review'),
        ('COMMITTEE_REVIEW', 'Committee Review'),
        ('APPROVED', 'Approved'),
        ('DISBURSED', 'Disbursed'),
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
            from django.db import transaction
            with transaction.atomic():
                # Acquire lock on last record to prevent race condition
                last = LoanApplication.objects.select_for_update().order_by('-id').first()
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
        LoanApplication, on_delete=models.CASCADE, related_name='status_history')
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

class RiskAssessment(models.Model):
    RISK_CATEGORY_CHOICES = [
        ('LOW', 'Low Risk'),
        ('MEDIUM', 'Medium Risk'),
        ('HIGH', 'High Risk'),
    ]

    application = models.OneToOneField(
        LoanApplication, on_delete=models.CASCADE, related_name='risk_assessment')
    risk_score = models.FloatField()                      # 0.0 – 100.0
    risk_category = models.CharField(max_length=10, choices=RISK_CATEGORY_CHOICES)
    confidence = models.FloatField(default=0.0)          # AI confidence 0.0 – 1.0
    ai_rationale = models.TextField()                    # Human-readable explanation

    # Factor breakdown (what contributed to the score)
    dti_score = models.FloatField(default=0)
    lti_score = models.FloatField(default=0)
    kyc_score = models.FloatField(default=0)
    income_stability_score = models.FloatField(default=0)
    repayment_history_score = models.FloatField(default=0)
    dependents_score = models.FloatField(default=0)

    # Early default signals
    default_signals = models.JSONField(default=list)

    # Who reviewed this (Risk Analyst)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviewed_risks'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    analyst_notes = models.TextField(blank=True)

    # Generated by
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.application.application_number} - {self.risk_category} ({self.risk_score})"

    class Meta:
        db_table = 'risk_assessments'


class RiskScoreHistory(models.Model):
    """Tracks all risk scores for a client over time (across multiple loans)."""
    client = models.ForeignKey(
        'clients.Client', on_delete=models.CASCADE, related_name='risk_history'
    )
    application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE)
    risk_score = models.FloatField()
    risk_category = models.CharField(max_length=10)
    scored_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'risk_score_history'
        ordering = ['-scored_at']


class CreditMemo(models.Model):
    """Summary document generated for Risk Analyst and Branch Manager review."""
    application = models.OneToOneField(
        LoanApplication, on_delete=models.CASCADE, related_name='credit_memo'
    )
    content = models.TextField()            # Full formatted memo text
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by_agent = models.CharField(max_length=10, default='A2')

    class Meta:
        db_table = 'credit_memos'



class AIRecommendation(models.Model):
    RECOMMENDATION_CHOICES = [
        ('RECOMMEND_APPROVAL', 'Recommend Approval'),
        ('RECOMMEND_REJECTION', 'Recommend Rejection'),
        ('RECOMMEND_REDUCED_AMOUNT', 'Recommend Reduced Amount'),
        ('RECOMMEND_MORE_DOCUMENTS', 'Recommend More Documents'),
        ('RECOMMEND_ESCALATION', 'Recommend Escalation to Manager'),
    ]

    OFFICER_DECISION_CHOICES = [
        ('ACCEPTED', 'Accepted AI Recommendation'),
        ('OVERRIDDEN', 'Overridden by Officer'),
        ('PENDING', 'Pending Review'),
    ]

    application = models.OneToOneField(
        LoanApplication, on_delete=models.CASCADE, related_name='ai_recommendation'
    )
    recommendation_type = models.CharField(max_length=40, choices=RECOMMENDATION_CHOICES)
    recommended_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    recommended_duration_months = models.IntegerField(null=True, blank=True)
    explanation = models.TextField()             # Plain-language explanation for staff
    reasons = models.JSONField(default=list)     # List of specific reason strings
    confidence = models.FloatField()

    # Officer response
    officer_decision = models.CharField(
        max_length=20, choices=OFFICER_DECISION_CHOICES, default='PENDING'
    )
    officer_override_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviewed_recommendations'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.application.application_number} → {self.recommendation_type}"

    class Meta:
        db_table = 'ai_recommendations'


class OfficerFeedback(models.Model):
    """Stores officer feedback on AI recommendation quality — used to improve A3 over time."""
    recommendation = models.ForeignKey(
        AIRecommendation, on_delete=models.CASCADE, related_name='feedback'
    )
    officer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    was_helpful = models.BooleanField()
    comment = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'officer_feedback'


class Loan(models.Model):
    """
    Active loan record — created only after disbursement is processed.
    """
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('CLOSED', 'Closed'),
        ('DEFAULTED', 'Defaulted'),
        ('WRITTEN_OFF', 'Written Off'),
        ('RESCHEDULED', 'Rescheduled'),
    ]

    loan_number = models.CharField(max_length=20, unique=True, blank=True)
    application = models.OneToOneField(
        LoanApplication, on_delete=models.PROTECT, related_name='loan'
    )
    client = models.ForeignKey(
        'clients.Client', on_delete=models.PROTECT, related_name='loans'
    )
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    duration_months = models.IntegerField()
    monthly_installment = models.DecimalField(max_digits=12, decimal_places=2)
    total_repayable = models.DecimalField(max_digits=12, decimal_places=2)
    outstanding_balance = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    disbursed_at = models.DateTimeField()
    expected_closure_date = models.DateField()
    actual_closure_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.loan_number:
            from django.db import transaction
            with transaction.atomic():
                # Acquire lock on last record to prevent race condition
                last = Loan.objects.select_for_update().order_by('-id').first()
                next_id = (last.id + 1) if last else 1
                self.loan_number = f"LN{str(next_id).zfill(7)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.loan_number} - {self.client} [{self.status}]"

    class Meta:
        db_table = 'loans'


class DisbursementCondition(models.Model):
    """Pre-disbursement checklist that Finance Staff must verify."""
    application = models.ForeignKey(
        LoanApplication, on_delete=models.CASCADE, related_name='disbursement_conditions'
    )
    condition_text = models.CharField(max_length=255)
    is_met = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'disbursement_conditions'


class Disbursement(models.Model):
    """Financial record of the actual disbursement transaction."""
    METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('MOBILE_MONEY', 'Mobile Money'),
        ('CHEQUE', 'Cheque'),
    ]

    application = models.OneToOneField(
        LoanApplication, on_delete=models.PROTECT, related_name='disbursement'
    )
    loan = models.OneToOneField(Loan, on_delete=models.PROTECT, related_name='disbursement_record')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='CASH')
    reference_number = models.CharField(max_length=100, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=50, blank=True)

    # Authorization
    authorized_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True,
        related_name='authorized_disbursements'
    )
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True,
        related_name='processed_disbursements'
    )

    disbursed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Disbursement: {self.application.application_number} - LKR {self.amount}"

    class Meta:
        db_table = 'disbursements'