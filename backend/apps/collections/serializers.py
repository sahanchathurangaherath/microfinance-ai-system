from rest_framework import serializers
from .models import DelinquencyCase, CollectionAction, PromiseToPay, EscalationRecord


class CollectionActionSerializer(serializers.ModelSerializer):
    performed_by_name = serializers.CharField(
        source='performed_by.get_full_name', read_only=True
    )

    class Meta:
        model = CollectionAction
        fields = '__all__'
        read_only_fields = ['case', 'performed_by', 'performed_at']


class PromiseToPaySerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.CharField(
        source='recorded_by.get_full_name', read_only=True
    )

    class Meta:
        model = PromiseToPay
        fields = '__all__'
        read_only_fields = ['case', 'recorded_by', 'recorded_at']


class EscalationSerializer(serializers.ModelSerializer):
    escalated_by_name = serializers.CharField(
        source='escalated_by.get_full_name', read_only=True
    )
    escalated_to_name = serializers.CharField(
        source='escalated_to.get_full_name', read_only=True
    )

    class Meta:
        model = EscalationRecord
        fields = '__all__'
        read_only_fields = ['case', 'escalated_by', 'escalated_at']


class DelinquencyCaseSerializer(serializers.ModelSerializer):
    loan_number = serializers.CharField(source='loan.loan_number', read_only=True)
    client_name = serializers.SerializerMethodField()
    client_phone = serializers.CharField(
        source='loan.client.phone_primary', read_only=True
    )
    assigned_to_name = serializers.CharField(
        source='assigned_to.get_full_name', read_only=True
    )
    actions = CollectionActionSerializer(many=True, read_only=True)
    promises = PromiseToPaySerializer(many=True, read_only=True)
    escalations = EscalationSerializer(many=True, read_only=True)

    class Meta:
        model = DelinquencyCase
        fields = '__all__'

    def get_client_name(self, obj):
        c = obj.loan.client
        return f"{c.first_name} {c.last_name}"