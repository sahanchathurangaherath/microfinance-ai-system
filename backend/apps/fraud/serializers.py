from rest_framework import serializers
from .models import FraudAlert, FraudInvestigation, ComplianceAction


class ComplianceActionSerializer(serializers.ModelSerializer):
    authorized_by_name = serializers.CharField(
        source='authorized_by.get_full_name', read_only=True
    )
    class Meta:
        model = ComplianceAction
        fields = '__all__'


class FraudInvestigationSerializer(serializers.ModelSerializer):
    investigator_name = serializers.CharField(
        source='investigator.get_full_name', read_only=True
    )
    class Meta:
        model = FraudInvestigation
        fields = '__all__'


class FraudAlertSerializer(serializers.ModelSerializer):
    client_name = serializers.SerializerMethodField()
    investigation = FraudInvestigationSerializer(read_only=True)
    compliance_actions = ComplianceActionSerializer(many=True, read_only=True)

    class Meta:
        model = FraudAlert
        fields = '__all__'

    def get_client_name(self, obj):
        if obj.client:
            return f"{obj.client.first_name} {obj.client.last_name}"
        return None