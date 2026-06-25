from rest_framework import serializers
from .models import Client, ClientAddress, ClientBusiness, ClientIncome
from apps.kyc.serializers import KYCDocumentSerializer, KYCChecklistSerializer


class ClientAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientAddress
        fields = '__all__'
        read_only_fields = ['client']


class ClientBusinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientBusiness
        fields = '__all__'
        read_only_fields = ['client']


class ClientIncomeSerializer(serializers.ModelSerializer):
    net_monthly_income = serializers.ReadOnlyField()

    class Meta:
        model = ClientIncome
        fields = '__all__'
        read_only_fields = ['client']


class ClientListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing clients."""
    registered_by_name = serializers.CharField(source='registered_by.get_full_name', read_only=True)

    class Meta:
        model = Client
        fields = [
            'id', 'client_number', 'nic_number', 'first_name', 'last_name',
            'phone_primary', 'status', 'data_quality_score',
            'registered_by_name', 'created_at'
        ]


class ClientDetailSerializer(serializers.ModelSerializer):
    """Full client detail including nested related data."""
    addresses = ClientAddressSerializer(many=True, read_only=True)
    business = ClientBusinessSerializer(read_only=True)
    income = ClientIncomeSerializer(read_only=True)
    documents = KYCDocumentSerializer(many=True, read_only=True)
    kyc_checklist = KYCChecklistSerializer(read_only=True)
    registered_by_name = serializers.CharField(source='registered_by.get_full_name', read_only=True)

    class Meta:
        model = Client
        fields = '__all__'


class CreateClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [
            'nic_number', 'first_name', 'last_name', 'date_of_birth',
            'gender', 'phone_primary', 'phone_secondary', 'email'
        ]

    def validate_nic_number(self, value):
        if Client.objects.filter(nic_number=value).exists():
            raise serializers.ValidationError(
                "A client with this NIC number already exists. Duplicate NIC detected."
            )
        return value