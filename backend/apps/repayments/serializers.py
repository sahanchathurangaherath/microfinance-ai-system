from rest_framework import serializers
from .models import RepaymentSchedule, RepaymentInstallment, Payment, PaymentReceipt


class InstallmentSerializer(serializers.ModelSerializer):
    outstanding = serializers.SerializerMethodField()
    loan_number = serializers.CharField(source='schedule.loan.loan_number', read_only=True)
    client_name = serializers.SerializerMethodField()
    total_amount_due = serializers.DecimalField(source='amount_due', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = RepaymentInstallment
        fields = '__all__'

    def get_outstanding(self, obj):
        return str(obj.amount_due - obj.amount_paid)

    def get_client_name(self, obj):
        try:
            return f"{obj.schedule.loan.client.first_name} {obj.schedule.loan.client.last_name}"
        except AttributeError:
            return "Unknown"


class PaymentSerializer(serializers.ModelSerializer):
    received_by_name = serializers.CharField(source='received_by.get_full_name', read_only=True)

    class Meta:
        model = Payment
        fields = '__all__'


class PaymentReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentReceipt
        fields = '__all__'