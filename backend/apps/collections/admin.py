from django.contrib import admin
from .models import DelinquencyCase, CollectionAction, PromiseToPay, EscalationRecord


@admin.register(DelinquencyCase)
class DelinquencyCaseAdmin(admin.ModelAdmin):
    list_display = ['id', 'loan', 'status', 'bucket', 'days_overdue', 'opened_at']
    list_filter = ['status', 'bucket', 'opened_at']
    search_fields = ['loan__loan_number']
    readonly_fields = ['opened_at', 'updated_at', 'resolved_at']


@admin.register(CollectionAction)
class CollectionActionAdmin(admin.ModelAdmin):
    list_display = ['id', 'case', 'action_type', 'outcome', 'performed_at']
    list_filter = ['action_type', 'outcome', 'performed_at']
    search_fields = ['case__loan__loan_number']
    readonly_fields = ['performed_at']


@admin.register(PromiseToPay)
class PromiseToPayAdmin(admin.ModelAdmin):
    list_display = ['id', 'case', 'promised_amount', 'promised_date', 'status']
    list_filter = ['status', 'recorded_at']
    search_fields = ['case__loan__loan_number']
    readonly_fields = ['recorded_at', 'fulfilled_at']


@admin.register(EscalationRecord)
class EscalationRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'case', 'reason', 'escalated_by', 'escalated_to', 'escalated_at']
    list_filter = ['reason', 'escalated_at', 'resolved']
    search_fields = ['case__loan__loan_number']
    readonly_fields = ['escalated_at', 'resolved_at']
