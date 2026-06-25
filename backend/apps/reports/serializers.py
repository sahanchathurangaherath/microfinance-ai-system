from rest_framework import serializers
from .models import ReportSnapshot, KPIRecord


class ReportSnapshotSerializer(serializers.ModelSerializer):
    """Serializer for point-in-time report snapshots."""
    
    class Meta:
        model = ReportSnapshot
        fields = [
            'id', 'report_type', 'data', 'generated_at', 'generated_by',
            'period_start', 'period_end'
        ]
        read_only_fields = ['generated_at', 'id']


class KPIRecordSerializer(serializers.ModelSerializer):
    """Serializer for key performance indicator tracking."""
    
    class Meta:
        model = KPIRecord
        fields = [
            'id', 'kpi_name', 'value', 'recorded_at', 'period'
        ]
        read_only_fields = ['recorded_at', 'id']


class ReportDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for report snapshots with calculated metrics."""
    
    metric_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ReportSnapshot
        fields = [
            'id', 'report_type', 'data', 'generated_at', 'generated_by',
            'period_start', 'period_end', 'metric_count'
        ]
        read_only_fields = ['generated_at', 'id']
    
    def get_metric_count(self, obj):
        """Count the number of metrics in the report data."""
        if isinstance(obj.data, dict):
            return len(obj.data)
        return 0
