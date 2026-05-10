from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    ACTION_TYPES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('AI_ACTION', 'AI Agent Action'),
        ('APPROVAL', 'Approval Decision'),
        ('DISBURSEMENT', 'Disbursement'),
        ('PAYMENT', 'Payment'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='audit_logs'
    )
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=50, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    extra_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"[{self.action_type}] {self.model_name} by {self.user} at {self.timestamp}"

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']