from rest_framework import serializers
from .models import RepaymentSchedule, RepaymentInstallment, Payment, PaymentReceipt


class InstallmentSerializer(serializers.ModelSerializer):
    outstanding = serializers.SerializerMethodField()

    class Meta:
        model = RepaymentInstallment
        fields = '__all__'

    def get_outstanding(self, obj):
        return str(obj.amount_due - obj.amount_paid)


class PaymentSerializer(serializers.ModelSerializer):
    received_by_name = serializers.CharField(source='received_by.get_full_name', read_only=True)

    class Meta:
        model = Payment
        fields = '__all__'


class PaymentReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentReceipt
        fields = '__all__'