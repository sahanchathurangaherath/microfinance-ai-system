from django.db import models
from django.conf import settings
from apps.clients.models import Client


class KYCDocument(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ('NIC_FRONT', 'NIC - Front'),
        ('NIC_BACK', 'NIC - Back'),
        ('PROOF_OF_ADDRESS', 'Proof of Address'),
        ('PROOF_OF_INCOME', 'Proof of Income'),
        ('BUSINESS_REG', 'Business Registration'),
        ('BANK_STATEMENT', 'Bank Statement'),
        ('PHOTO', 'Passport Photo'),
        ('OTHER', 'Other'),
    ]

    STATUS_CHOICES = [
        ('UPLOADED', 'Uploaded'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES)
    file = models.FileField(upload_to='kyc_documents/%Y/%m/')
    file_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UPLOADED')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_documents'
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='verified_documents'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client.client_number} - {self.document_type}"

    class Meta:
        db_table = 'kyc_documents'


class KYCChecklist(models.Model):
    """Tracks which KYC items have been completed for a client."""

    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name='kyc_checklist')

    # Identity
    nic_verified = models.BooleanField(default=False)
    photo_verified = models.BooleanField(default=False)

    # Address
    address_verified = models.BooleanField(default=False)

    # Financial
    income_verified = models.BooleanField(default=False)
    bank_statement_verified = models.BooleanField(default=False)

    # Business (optional for non-business clients)
    business_reg_verified = models.BooleanField(default=False)
    business_verified_not_applicable = models.BooleanField(default=False)

    # Compliance
    aml_check_done = models.BooleanField(default=False)
    sanctions_check_done = models.BooleanField(default=False)

    # Status
    is_complete = models.BooleanField(default=False)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def calculate_completion(self):
        """
        Returns how complete this KYC checklist is as a percentage.
        Business check is excluded if not applicable.
        """
        checks = [
            self.nic_verified,
            self.photo_verified,
            self.address_verified,
            self.income_verified,
            self.bank_statement_verified,
            self.aml_check_done,
            self.sanctions_check_done,
        ]
        if not self.business_verified_not_applicable:
            checks.append(self.business_reg_verified)

        completed = sum(1 for c in checks if c)
        return round((completed / len(checks)) * 100, 1)

    def __str__(self):
        return f"KYC Checklist - {self.client.client_number}"

    class Meta:
        db_table = 'kyc_checklists'