from django.contrib import admin
from .models import (
    AgentActionLog, HumanDecisionLog, AIServiceStatus,
    SystemIncident, ManualReviewCase, AgentConfiguration, AgentConfigChangeLog
)

@admin.register(AgentConfiguration)
class AgentConfigurationAdmin(admin.ModelAdmin):
    list_display = ('agent_id', 'llm_enabled', 'is_paused', 'confidence_threshold', 'model_override', 'fallback_behavior', 'daily_token_budget', 'last_changed_by', 'last_changed_at')
    list_filter = ('llm_enabled', 'is_paused')
    search_fields = ('agent_id', 'model_override')

@admin.register(AgentConfigChangeLog)
class AgentConfigChangeLogAdmin(admin.ModelAdmin):
    list_display = ('agent_id', 'field_changed', 'old_value', 'new_value', 'changed_by', 'changed_at')
    list_filter = ('agent_id', 'field_changed')
    search_fields = ('agent_id', 'field_changed', 'reason')
    readonly_fields = ('agent_id', 'field_changed', 'old_value', 'new_value', 'changed_by', 'reason', 'changed_at')

@admin.register(AgentActionLog)
class AgentActionLogAdmin(admin.ModelAdmin):
    list_display = ('agent_id', 'agent_name', 'status', 'confidence', 'execution_mode', 'ai_bypassed', 'invoked_at')
    list_filter = ('agent_id', 'status', 'execution_mode', 'ai_bypassed')
    search_fields = ('agent_id', 'agent_name', 'input_reference', 'bypass_reason')

@admin.register(HumanDecisionLog)
class HumanDecisionLogAdmin(admin.ModelAdmin):
    list_display = ('officer', 'decision_type', 'decision', 'followed_ai', 'decided_at')
    list_filter = ('decision_type', 'followed_ai')
    search_fields = ('officer__username', 'reference_model', 'reference_id', 'reason')

@admin.register(AIServiceStatus)
class AIServiceStatusAdmin(admin.ModelAdmin):
    list_display = ('status', 'last_checked', 'last_online', 'consecutive_failures', 'manual_mode_active')

@admin.register(SystemIncident)
class SystemIncidentAdmin(admin.ModelAdmin):
    list_display = ('incident_type', 'severity', 'status', 'agent_id', 'occurred_at')
    list_filter = ('severity', 'status', 'agent_id')
    search_fields = ('incident_type', 'error_message', 'affected_reference')

@admin.register(ManualReviewCase)
class ManualReviewCaseAdmin(admin.ModelAdmin):
    list_display = ('agent_id', 'reference_model', 'reference_id', 'status', 'assigned_to', 'created_at')
    list_filter = ('status', 'agent_id')
    search_fields = ('reference_model', 'manual_notes', 'manual_decision')
