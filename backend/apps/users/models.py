from django.contrib.auth.models import AbstractUser
from django.db import models


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

    def has_role(self, *roles):
        """Helper: check if user has one of the given roles."""
        return self.role in roles

    class Meta:
        db_table = 'users'


class UserActivityLog(models.Model):
    ACTION_CHOICES = [
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('FAILED_LOGIN', 'Failed Login Attempt'),
        ('PASSWORD_CHANGE', 'Password Change'),
        ('PROFILE_UPDATE', 'Profile Update'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activity_logs'
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    detail = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} at {self.timestamp}"

    class Meta:
        db_table = 'user_activity_logs'
        ordering = ['-timestamp']