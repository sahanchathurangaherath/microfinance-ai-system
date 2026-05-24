from rest_framework import serializers
from .models import LoanApplication, CashflowAssessment, LoanDocument, ApplicationStatusHistory, LoanProduct
from apps.clients.serializers import ClientListSerializer


class LoanProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanProduct
        fields = '__all__'


class CashflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashflowAssessment
        fields = '__all__'
        read_only_fields = ['application', 'debt_to_income_ratio', 'net_cashflow']


class LoanDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanDocument
        fields = '__all__'
        read_only_fields = ['application', 'uploaded_by']


class StatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)

    class Meta:
        model = ApplicationStatusHistory
        fields = '__all__'


class LoanApplicationListSerializer(serializers.ModelSerializer):
    client_name = serializers.SerializerMethodField()
    client_number = serializers.CharField(source='client.client_number', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = LoanApplication
        fields = [
            'id', 'application_number', 'client_name', 'client_number',
            'requested_amount', 'requested_duration_months', 'loan_purpose',
            'status', 'status_display', 'created_by_name', 'created_at', 'submitted_at'
        ]

    def get_client_name(self, obj):
        return f"{obj.client.first_name} {obj.client.last_name}"


class LoanApplicationDetailSerializer(serializers.ModelSerializer):
    client = ClientListSerializer(read_only=True)
    cashflow = CashflowSerializer(read_only=True)
    documents = LoanDocumentSerializer(many=True, read_only=True)
    status_history = StatusHistorySerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = LoanApplication
        fields = '__all__'


class CreateLoanApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanApplication
        fields = [
            'client', 'loan_product', 'requested_amount',
            'requested_duration_months', 'loan_purpose',
            'purpose_description', 'officer_notes'
        ]

    def validate(self, data):
        client = data.get('client')
        # Client must be VERIFIED or ACTIVE to apply for a loan
        if client.status not in ['VERIFIED', 'ACTIVE']:
            raise serializers.ValidationError(
                f"Client status is '{client.status}'. Client must be VERIFIED before a loan application can be created."
            )
        return data