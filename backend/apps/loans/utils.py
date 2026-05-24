from .models import ApplicationStatusHistory


def log_status_change(application, from_status, to_status, user, reason=""):
    """
    Records every status transition on a loan application.
    This is the audit trail for the full loan lifecycle.
    """
    ApplicationStatusHistory.objects.create(
        application=application,
        from_status=from_status,
        to_status=to_status,
        changed_by=user,
        changed_by_role=user.role if user else '',
        reason=reason
    )
    application.status = to_status
    application.save()