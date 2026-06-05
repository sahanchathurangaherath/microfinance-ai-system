from rest_framework import serializers
from .models import NotificationQueue, NotificationLog, NotificationTemplate


class NotificationQueueSerializer(serializers.ModelSerializer):
    approved_by_name = serializers.CharField(
        source='approved_by.get_full_name', read_only=True
    )

    class Meta:
        model = NotificationQueue
        fields = '__all__'


class NotificationLogSerializer(serializers.ModelSerializer):
    notification_channel = serializers.CharField(
        source='notification.channel', read_only=True
    )
    notification_type = serializers.CharField(
        source='notification.comm_type', read_only=True
    )

    class Meta:
        model = NotificationLog
        fields = '__all__'


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = '__all__'