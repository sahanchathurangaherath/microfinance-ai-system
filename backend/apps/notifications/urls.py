from django.urls import path
from .views import (
    DraftNotificationView, PendingApprovalView,
    ApproveNotificationView, RejectNotificationView,
    SendNotificationView, NotificationLogListView
)

urlpatterns = [
    path('draft/', DraftNotificationView.as_view()),
    path('pending/', PendingApprovalView.as_view()),
    path('<int:notif_id>/approve/', ApproveNotificationView.as_view()),
    path('<int:notif_id>/reject/', RejectNotificationView.as_view()),
    path('<int:notif_id>/send/', SendNotificationView.as_view()),
    path('logs/', NotificationLogListView.as_view()),
]