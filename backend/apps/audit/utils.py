"""
Audit logging utility functions for recording actions, AI interactions, and human decisions.
"""

from .models import AuditLog, AgentActionLog, HumanDecisionLog


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


def log_action(
    user,
    action_type,
    model_name='',
    object_id='',
    description='',
    status_before='',
    status_after='',
    request=None,
    extra_data=None
):
    """
    Log a general action in the audit trail.
    
    Args:
        user: User performing the action
        action_type: Type of action (from AuditLog.ACTION_TYPES)
        model_name: Django model name being acted on
        object_id: ID of the object being acted on
        description: Human-readable description
        status_before: Previous status (for status changes)
        status_after: New status (for status changes)
        request: HTTP request object (to extract IP, user agent)
        extra_data: Optional dict of additional context
    """
    ip_address = None
    user_agent = ''
    
    if request:
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    AuditLog.objects.create(
        user=user,
        action_type=action_type,
        model_name=model_name,
        object_id=object_id,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        status_before=status_before,
        status_after=status_after,
        extra_data=extra_data or {}
    )


def log_agent_action(
    agent_id,
    agent_name,
    input_reference='',
    input_payload=None,
    output_payload=None,
    confidence=None,
    status='SUCCESS',
    rationale='',
    triggered_by=None,
    response_time_ms=None,
    trigger_type='automatic',
    llm_model_used='',
    prompt_tokens_used=0,
    completion_tokens_used=0,
    llm_raw_response='',
    hallucination_check_passed=True,
    execution_mode='',
    ai_bypassed=False,
    bypass_reason='',
):
    """
    Log an AI agent action with full traceability.
    """
    import hashlib
    import json
    
    # Compute input hash for traceability
    input_payload_dict = input_payload or {}
    input_str = json.dumps(input_payload_dict, default=str, sort_keys=True)
    input_hash = hashlib.sha256(input_str.encode()).hexdigest()
    
    AgentActionLog.objects.create(
        agent_id=agent_id,
        agent_name=agent_name,
        triggered_by=triggered_by,
        trigger_type=trigger_type,
        input_reference=input_reference,
        input_hash=input_hash,
        input_payload=input_payload_dict,
        output_payload=output_payload or {},
        confidence=confidence,
        status=status,
        rationale=rationale,
        response_time_ms=response_time_ms,
        llm_model_used=llm_model_used,
        prompt_tokens_used=prompt_tokens_used,
        completion_tokens_used=completion_tokens_used,
        llm_raw_response=llm_raw_response,
        hallucination_check_passed=hallucination_check_passed,
        execution_mode=execution_mode,
        ai_bypassed=ai_bypassed,
        bypass_reason=bypass_reason,
    )


def log_human_decision(
    officer,
    decision_type,
    reference_model='',
    reference_id='',
    decision='',
    reason='',
    ai_recommendation='',
    followed_ai=None,
    override_justification='',
    officer_role=''
):
    """
    Log a human approval/decision with AI comparison.
    
    Args:
        officer: User making the decision
        decision_type: Type from HumanDecisionLog.DECISION_TYPES
        reference_model: Model being decided upon (e.g., 'LoanApplication')
        reference_id: ID of the model instance
        decision: Decision outcome (APPROVED, REJECTED, etc.)
        reason: Justification for the decision
        ai_recommendation: What the AI recommended
        followed_ai: Boolean whether officer followed AI
        override_justification: Why they overrode AI (if applicable)
        officer_role: Role of the officer (optional)
    """
    HumanDecisionLog.objects.create(
        officer=officer,
        officer_role=officer_role or getattr(officer, 'role', ''),
        decision_type=decision_type,
        reference_model=reference_model,
        reference_id=str(reference_id),
        decision=decision,
        reason=reason,
        ai_recommendation=ai_recommendation,
        followed_ai=followed_ai,
        override_justification=override_justification
    )
