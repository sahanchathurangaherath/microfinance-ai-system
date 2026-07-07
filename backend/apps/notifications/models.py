from django.db import models
from django.conf import settings
from apps.clients.models import Client


class NotificationTemplate(models.Model):
    COMM_TYPE_CHOICES = [
        ('REPAYMENT_REMINDER', 'Repayment Reminder'),
        ('OVERDUE_REMINDER', 'Overdue Payment Reminder'),
        ('PTP_REMINDER', 'Promise to Pay Reminder'),
        ('LOAN_APPROVED', 'Loan Approval Notification'),
        ('LOAN_REJECTED', 'Loan Rejection Notification'),
        ('STAFF_ESCALATION_ALERT', 'Staff Escalation Alert'),
        ('FRAUD_ALERT_NOTIFY', 'Fraud Alert Notification'),
        ('GENERAL', 'General Communication'),
    ]

    CHANNEL_CHOICES = [
        ('SMS', 'SMS'),
        ('EMAIL', 'Email'),
        ('BOTH', 'SMS and Email'),
    ]

    comm_type = models.CharField(max_length=30, choices=COMM_TYPE_CHOICES)
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default='BOTH')
    sms_template = models.TextField()
    email_subject_template = models.CharField(max_length=255)
    email_body_template = models.TextField()
    language = models.CharField(max_length=10, default='en')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.comm_type} ({self.channel})"

    class Meta:
        db_table = 'notification_templates'
        unique_together = ['comm_type', 'language']


class NotificationQueue(models.Model):
    STATUS_CHOICES = [
        ('PENDING_APPROVAL', 'Pending Officer Approval'),
        ('APPROVED', 'Approved — Ready to Send'),
        ('REJECTED', 'Rejected by Officer'),
        ('SENT', 'Sent'),
        ('FAILED', 'Send Failed'),
        ('CANCELLED', 'Cancelled'),
    ]

    CHANNEL_CHOICES = [
        ('SMS', 'SMS'),
        ('EMAIL', 'Email'),
    ]

    client = models.ForeignKey(
        Client, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='notifications'
    )
    recipient_phone = models.CharField(max_length=20, blank=True)
    recipient_email = models.EmailField(blank=True)
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)
    comm_type = models.CharField(max_length=30)

    # A6 generated content
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    ai_drafted = models.BooleanField(default=True)
    ai_rationale = models.TextField(blank=True)

    # Approval
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING_APPROVAL')
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_notifications'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    # Reference context
    reference_type = models.CharField(max_length=50, blank=True)  # e.g., "loan", "case"
    reference_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"[{self.channel}] {self.comm_type} → {self.recipient_phone or self.recipient_email} [{self.status}]"

    class Meta:
        db_table = 'notification_queue'
        ordering = ['-created_at']


class NotificationLog(models.Model):
    """Permanent record of every sent or failed notification."""
    notification = models.OneToOneField(
        NotificationQueue, on_delete=models.CASCADE, related_name='log'
    )
    delivered = models.BooleanField(default=False)
    delivery_timestamp = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    provider_reference = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'notification_logs'


class UserNotification(models.Model):
    """In-app notification for a staff user (loan officer, admin, etc.)."""

    TYPE_CHOICES = [
        ('INFO', 'Info'),
        ('SUCCESS', 'Success'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('FRAUD_ALERT', 'Fraud Alert'),
        ('LOAN_STATUS', 'Loan Status'),
        ('APPROVAL_REQUIRED', 'Approval Required'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_notifications'
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='INFO')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional link to a related object
    link_url = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"[{self.notification_type}] {self.title} → {self.recipient} (read={self.is_read})"

    class Meta:
        db_table = 'user_notifications'
        ordering = ['-created_at']