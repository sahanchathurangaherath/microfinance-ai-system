from django.urls import path
from .views import (
    DraftNotificationView, PendingApprovalView,
    ApproveNotificationView, RejectNotificationView,
    SendNotificationView, NotificationLogListView,
    NotificationQueueListView,
    UserNotificationListView, UserNotificationMarkReadView, UserNotificationMarkAllReadView,
)

urlpatterns = [
    # ── In-app user notifications (used by frontend) ──────────────────────────
    path('', UserNotificationListView.as_view(), name='user_notifications'),
    path('<int:pk>/read', UserNotificationMarkReadView.as_view(), name='user_notification_mark_read'),
    path('mark-all-read', UserNotificationMarkAllReadView.as_view(), name='user_notification_mark_all_read'),

    # ── Staff communication workflow (SMS/Email to clients) ───────────────────
    path('queue', NotificationQueueListView.as_view(), name='notification_queue'),
    path('draft', DraftNotificationView.as_view(), name='notification_draft'),
    path('pending', PendingApprovalView.as_view(), name='notification_pending'),
    path('<int:notif_id>/approve', ApproveNotificationView.as_view(), name='notification_approve'),
    path('<int:notif_id>/reject', RejectNotificationView.as_view(), name='notification_reject'),
    path('<int:notif_id>/send', SendNotificationView.as_view(), name='notification_send'),
    path('logs', NotificationLogListView.as_view(), name='notification_logs'),
]