from django.contrib.auth.models import AbstractUser
from django.db import models

class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'roles'


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'System Administrator'),
        ('loan_officer', 'Loan Officer'),
        ('risk_analyst', 'Risk Analyst'),
        ('branch_manager', 'Branch Manager'),
        ('credit_committee', 'Credit Committee Member'),
        ('collections_officer', 'Collections Officer'),
        ('compliance_officer', 'Compliance Officer'),
        ('finance_staff', 'Finance Staff'),
    ]

    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='loan_officer')
    phone = models.CharField(max_length=20, blank=True)
    branch = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    class Meta:
        db_table = 'users'