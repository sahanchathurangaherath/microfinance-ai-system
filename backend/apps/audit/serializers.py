from rest_framework import serializers
from .models import (
    AuditLog, AgentActionLog, HumanDecisionLog, LoginAttempt,
    AIServiceStatus, SystemIncident, ManualReviewCase
)


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = AuditLog
        fields = '__all__'


class AgentActionLogSerializer(serializers.ModelSerializer):
    triggered_by_name = serializers.CharField(
        source='triggered_by.username', read_only=True
    )

    class Meta:
        model = AgentActionLog
        fields = '__all__'


class HumanDecisionLogSerializer(serializers.ModelSerializer):
    officer_name = serializers.CharField(source='officer.get_full_name', read_only=True)

    class Meta:
        model = HumanDecisionLog
        fields = '__all__'


class LoginAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginAttempt
        fields = '__all__'


class SystemIncidentSerializer(serializers.ModelSerializer):
    resolved_by_name = serializers.CharField(
        source='resolved_by.get_full_name', read_only=True
    )

    class Meta:
        model = SystemIncident
        fields = '__all__'


class ManualReviewCaseSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(
        source='assigned_to.get_full_name', read_only=True
    )

    class Meta:
        model = ManualReviewCase
        fields = '__all__'


class AIServiceStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIServiceStatus
        fields = '__all__'