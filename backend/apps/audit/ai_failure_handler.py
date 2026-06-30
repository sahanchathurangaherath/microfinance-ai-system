from django.utils import timezone
from .models import SystemIncident, ManualReviewCase, AIServiceStatus
import logging

logger = logging.getLogger(__name__)


def handle_ai_failure(
    agent_id: str,
    reference_model: str,
    reference_id: int,
    error_message: str,
    severity: str = 'HARD',
    triggered_by=None
):
    """
    Central handler for any AI agent failure.
    Call this inside every except block that catches AI service errors.

    Usage:
        try:
            response = httpx.post(...)
        except Exception as e:
            handle_ai_failure(
                agent_id='A2',
                reference_model='LoanApplication',
                reference_id=application.id,
                error_message=str(e),
                severity='HARD',
                triggered_by=request.user
            )
    """
    from decouple import config
    
    logger.error(
        f"AI Failure | Agent: {agent_id} | Ref: {reference_model}#{reference_id} | {error_message}"
    )

    # Determine if this was an LLM failure or rule-based failure
    llm_flag_map = {
        "A1": "A1_USE_LLM", "A2": "A2_USE_LLM", "A3": "A3_USE_LLM",
        "A4": "A4_USE_LLM", "A5": "A5_USE_LLM", "A6": "A6_USE_LLM",
    }
    llm_flag = llm_flag_map.get(agent_id, "")
    llm_active = config(llm_flag, default=False, cast=bool) if llm_flag else False
    llm_model = config("LOCAL_LLM_MODEL", default="qwen3:8b") if llm_active else "rule-based"

    # Create incident record with LLM context
    incident = SystemIncident.objects.create(
        incident_type=f"{agent_id}_FAILURE",
        severity=severity,
        agent_id=agent_id,
        affected_reference=f"{reference_model}:{reference_id}",
        error_message=f"[LLM: {llm_model}] {error_message}",
    )

    # Create or get manual review case (using get_or_create to avoid duplicates)
    manual_case, _ = ManualReviewCase.objects.get_or_create(
        reference_model=reference_model,
        reference_id=reference_id,
        agent_id=agent_id,
        defaults={
            "manual_notes": error_message,
            "incident": incident,
            "status": "PENDING",
        }
    )

    # Update AI service status counter
    status_obj, _ = AIServiceStatus.objects.get_or_create(pk=1)
    status_obj.consecutive_failures += 1
    if status_obj.consecutive_failures >= 3:
        status_obj.status = 'OFFLINE'
        status_obj.manual_mode_active = True
    status_obj.save()

    return incident, manual_case


def handle_ai_recovery():
    """
    Call this when a health check succeeds after failures.
    Resets service status and queues pending manual reviews for AI retry.
    """
    status_obj, _ = AIServiceStatus.objects.get_or_create(pk=1)
    status_obj.status = 'ONLINE'
    status_obj.consecutive_failures = 0
    status_obj.manual_mode_active = False
    status_obj.last_online = timezone.now()
    status_obj.save()

    # Queue all pending manual cases for AI retry
    pending = ManualReviewCase.objects.filter(
        status='PENDING', retry_after_recovery=True
    )
    count = pending.count()
    pending.update(status='AI_RETRY_QUEUED')

    logger.info(f"AI service recovered. {count} case(s) queued for retry.")
    return count