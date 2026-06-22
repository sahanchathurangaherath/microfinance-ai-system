from django.db import models
from django.conf import settings


class Client(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('KYC_SUBMITTED', 'KYC Submitted'),
        ('VERIFIED', 'Verified'),
        ('ACTIVE', 'Active'),
        ('REJECTED', 'Rejected'),
        ('SUSPENDED', 'Suspended'),
    ]

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    # Core identification
    client_number = models.CharField(max_length=20, unique=True, blank=True)
    nic_number = models.CharField(max_length=20, unique=True)  # Duplicate detection key
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)

    # Contact details
    phone_primary = models.CharField(max_length=20)
    phone_secondary = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    # Who registered this client
    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='registered_clients'
    )

    preferred_language = models.CharField(
    max_length=5,
    choices=[('en', 'English'), ('si', 'Sinhala'), ('ta', 'Tamil')],
    default='en'
)

    # A1 data quality score (set by AI agent)
    data_quality_score = models.FloatField(null=True, blank=True)
    data_quality_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Auto-generate client number before first save
        if not self.client_number:
            last = Client.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.client_number = f"CLT{str(next_id).zfill(6)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.client_number} - {self.first_name} {self.last_name}"

    class Meta:
        db_table = 'clients'
        ordering = ['-created_at']


class ClientAddress(models.Model):
    ADDRESS_TYPE_CHOICES = [
        ('HOME', 'Home'),
        ('BUSINESS', 'Business'),
        ('POSTAL', 'Postal'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPE_CHOICES, default='HOME')
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.client.client_number} - {self.address_type}"

    class Meta:
        db_table = 'client_addresses'


class ClientBusiness(models.Model):
    BUSINESS_TYPE_CHOICES = [
        ('SOLE_PROPRIETOR', 'Sole Proprietor'),
        ('PARTNERSHIP', 'Partnership'),
        ('PRIVATE_LIMITED', 'Private Limited'),
        ('INFORMAL', 'Informal Business'),
        ('FARMING', 'Farming'),
        ('OTHER', 'Other'),
    ]

    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name='business')
    business_name = models.CharField(max_length=255)
    business_type = models.CharField(max_length=50, choices=BUSINESS_TYPE_CHOICES)
    business_description = models.TextField(blank=True)
    years_in_operation = models.IntegerField(default=0)
    number_of_employees = models.IntegerField(default=0)
    business_address = models.TextField(blank=True)
    monthly_revenue = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.client.client_number} - {self.business_name}"

    class Meta:
        db_table = 'client_businesses'


class ClientIncome(models.Model):
    INCOME_SOURCE_CHOICES = [
        ('BUSINESS', 'Business Income'),
        ('SALARY', 'Salary'),
        ('AGRICULTURE', 'Agriculture'),
        ('REMITTANCE', 'Remittance'),
        ('PENSION', 'Pension'),
        ('OTHER', 'Other'),
    ]

    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name='income')
    income_source = models.CharField(max_length=50, choices=INCOME_SOURCE_CHOICES)
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2)
    other_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    monthly_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    existing_debt_monthly = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    number_of_dependents = models.IntegerField(default=0)

    @property
    def net_monthly_income(self):
        return self.monthly_income + self.other_income - self.monthly_expenses - self.existing_debt_monthly

    def __str__(self):
        return f"{self.client.client_number} - Income: {self.monthly_income}"

    class Meta:
        db_table = 'client_incomes'