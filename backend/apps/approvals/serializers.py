from rest_framework import serializers
from .models import ApprovalWorkflow, ApprovalDecision, CommitteeDecision


class ApprovalDecisionSerializer(serializers.ModelSerializer):
    decided_by_name = serializers.CharField(source='decided_by.get_full_name', read_only=True)
    decided_by_role = serializers.CharField(source='decided_by.role', read_only=True)
    step_display = serializers.CharField(source='get_step_display', read_only=True)
    decision_display = serializers.CharField(source='get_decision_display', read_only=True)

    class Meta:
        model = ApprovalDecision
        fields = '__all__'


class CommitteeDecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommitteeDecision
        fields = '__all__'


class ApprovalWorkflowSerializer(serializers.ModelSerializer):
    decisions = ApprovalDecisionSerializer(many=True, read_only=True)
    committee_decision = CommitteeDecisionSerializer(read_only=True)
    application_number = serializers.CharField(
        source='application.application_number', read_only=True
    )
    client_name = serializers.SerializerMethodField()
    requested_amount = serializers.DecimalField(
        source='application.requested_amount',
        max_digits=12, decimal_places=2, read_only=True
    )
    risk_category = serializers.SerializerMethodField()
    ai_recommendation = serializers.SerializerMethodField()

    class Meta:
        model = ApprovalWorkflow
        fields = '__all__'

    def get_client_name(self, obj):
        c = obj.application.client
        return f"{c.first_name} {c.last_name}"

    def get_risk_category(self, obj):
        try:
            return obj.application.risk_assessment.risk_category
        except Exception:
            return None

    def get_ai_recommendation(self, obj):
        try:
            return obj.application.ai_recommendation.recommendation_type
        except Exception:
            return None