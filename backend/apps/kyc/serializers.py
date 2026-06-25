from rest_framework import serializers
from .models import KYCDocument, KYCChecklist


class KYCDocumentSerializer(serializers.ModelSerializer):
    """Serializer for KYC document uploads and verification."""
    class Meta:
        model = KYCDocument
        fields = '__all__'
        read_only_fields = ['client', 'uploaded_by', 'verified_by', 'verified_at']


class KYCChecklistSerializer(serializers.ModelSerializer):
    """Serializer for KYC checklist tracking and completion."""
    completion_percentage = serializers.SerializerMethodField()

    class Meta:
        model = KYCChecklist
        fields = '__all__'
        read_only_fields = ['client', 'is_complete', 'completed_by', 'completed_at']

    def get_completion_percentage(self, obj):
        return obj.calculate_completion()
