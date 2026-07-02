# backend/apps/audit/policy_engine.py
"""
Central Gatekeeper and Policy Evaluation Engine for AI Agents.
Decides whether an agent is allowed to execute based on live database settings.
Implements fail-safe fallbacks, disagreement checking, and manual review gates.
"""
import httpx
import json
import logging
from typing import Dict, Tuple
from django.conf import settings
from django.utils import timezone
from .models import AgentConfiguration, AgentActionLog, SystemIncident, ManualReviewCase
from .utils import log_agent_action
from .rules_fallback import run_local_rules
from apps.loans.models import RiskAssessment, AIRecommendation
from apps.fraud.models import FraudAlert

logger = logging.getLogger(__name__)


def evaluate_and_run_agent(
    agent_id: str,
    payload: Dict,
    triggered_by=None,
    input_reference: str = '',
    trigger_type: str = 'manual'
) -> Dict:
    """
    Evaluates policy gates and triggers AI agent or safe local rules fallback.
    Returns: Dict representing the standardized agent response structure.
    """
    # 1. Fetch live Agent Configuration (or create default row on the fly)
    agent_names = {
        "A1": "Data Collection Agent",
        "A2": "Risk Assessment Agent",
        "A3": "Recommendation Agent",
        "A4": "Monitoring Agent",
        "A5": "Fraud Detection Agent",
        "A6": "Communication Agent",
    }
    agent_name = agent_names.get(agent_id, f"Agent {agent_id}")
    
    cfg, _ = AgentConfiguration.objects.get_or_create(
        agent_id=agent_id,
        defaults={
            "llm_enabled": agent_id not in ["A1", "A4"],  # A1, A4 default to False (rule-based)
            "is_paused": False,
            "confidence_threshold": 0.65,
        }
    )

    # 2. Check PAUSED Kill Switch
    if cfg.is_paused:
        # Run local rules engine immediately
        rule_res = run_local_rules(agent_id, payload)
        
        # Log incident
        incident = SystemIncident.objects.create(
            incident_type=f"{agent_id}_PAUSED",
            severity="PARTIAL",
            agent_id=agent_id,
            affected_reference=input_reference,
            error_message=f"Agent was paused by admin. Reason: {cfg.pause_reason}",
        )
        # Create Manual Review Case
        ref_model, ref_id = parse_reference(input_reference)
        ManualReviewCase.objects.get_or_create(
            reference_model=ref_model,
            reference_id=ref_id,
            agent_id=agent_id,
            defaults={
                "manual_notes": f"Agent paused by admin. Reason: {cfg.pause_reason}",
                "incident": incident,
                "status": "PENDING"
            }
        )

        log_agent_action(
            agent_id=agent_id,
            agent_name=agent_name,
            input_reference=input_reference,
            input_payload=payload,
            output_payload=rule_res.get("output"),
            confidence=0.0,
            status="REQUIRES_HUMAN_REVIEW",
            rationale=f"Agent is paused by admin. Local rules run. Reason: {cfg.pause_reason}",
            triggered_by=triggered_by,
            trigger_type=trigger_type,
            execution_mode="RULE_ONLY",
            ai_bypassed=True,
            bypass_reason=f"Agent paused by admin: {cfg.pause_reason}",
        )
        return rule_res

    # 3. Check LLM Enabled Toggle
    if not cfg.llm_enabled:
        # Run rules (can try FastAPI with use_llm=False, but fallback to local rules if FastAPI is down)
        try:
            response = call_fastapi_agent(agent_id, payload, use_llm=False)
            execution_mode = "RULE_ONLY"
            ai_bypassed = True
            bypass_reason = "LLM disabled by policy"
        except Exception as e:
            logger.warning(f"FastAPI rule call failed for {agent_id}: {str(e)}. Running locally.")
            response = run_local_rules(agent_id, payload)
            execution_mode = "RULE_ONLY"
            ai_bypassed = True
            bypass_reason = f"LLM disabled by policy + FastAPI down: {str(e)}"

        log_agent_action(
            agent_id=agent_id,
            agent_name=agent_name,
            input_reference=input_reference,
            input_payload=payload,
            output_payload=response.get("output"),
            confidence=response.get("confidence", 0.0),
            status=response.get("status", "SUCCESS"),
            rationale=response.get("rationale", ""),
            triggered_by=triggered_by,
            trigger_type=trigger_type,
            execution_mode=execution_mode,
            ai_bypassed=ai_bypassed,
            bypass_reason=bypass_reason,
        )
        return response

    # 4. LLM Enabled — Hybrid Mode / AI Mode
    # Fetch rule baseline first (for comparison in Hybrid Mode)
    rule_res = run_local_rules(agent_id, payload)
    rule_out = rule_res.get("output") or {}

    try:
        # Call FastAPI Service with use_llm=True
        ai_res = call_fastapi_agent(agent_id, payload, use_llm=True)
        ai_out = ai_res.get("output") or {}
        confidence = ai_res.get("confidence", 0.0)

        # Disagreement and Gate Check
        disagreed, disagreement_reason = check_disagreement(agent_id, rule_out, ai_out)
        low_confidence = confidence < cfg.confidence_threshold
        risky = is_result_risky(agent_id, ai_out)

        requires_review = low_confidence or disagreed or risky
        status = "REQUIRES_HUMAN_REVIEW" if requires_review else ai_res.get("status", "SUCCESS")
        
        # Log detailed rationale if review is triggered
        gate_reasons = []
        if low_confidence: gate_reasons.append(f"AI confidence ({round(confidence, 2)}) below threshold ({cfg.confidence_threshold})")
        if disagreed: gate_reasons.append(f"Rules & AI disagreed: {disagreement_reason}")
        if risky: gate_reasons.append("Result classified as High Risk")

        rationale = ai_res.get("rationale", "")
        if gate_reasons:
            rationale = f"GATE TRIGGERED: {', '.join(gate_reasons)}. | " + rationale

        if requires_review:
            # Create Incident and Manual Review Case
            ref_model, ref_id = parse_reference(input_reference)
            incident = SystemIncident.objects.create(
                incident_type=f"{agent_id}_HUMAN_REVIEW_GATE",
                severity="SOFT",
                agent_id=agent_id,
                affected_reference=input_reference,
                error_message=f"Human review gate triggered: {', '.join(gate_reasons)}",
            )
            ManualReviewCase.objects.get_or_create(
                reference_model=ref_model,
                reference_id=ref_id,
                agent_id=agent_id,
                defaults={
                    "manual_notes": f"Gate Triggered: {', '.join(gate_reasons)}",
                    "incident": incident,
                    "status": "PENDING"
                }
            )

        log_agent_action(
            agent_id=agent_id,
            agent_name=agent_name,
            input_reference=input_reference,
            input_payload=payload,
            output_payload=ai_out,
            confidence=confidence,
            status=status,
            rationale=rationale,
            triggered_by=triggered_by,
            trigger_type=trigger_type,
            response_time_ms=None,
            llm_model_used=ai_res.get("usage_metadata", {}).get("model_used", ""),
            prompt_tokens_used=ai_res.get("usage_metadata", {}).get("prompt_tokens", 0),
            completion_tokens_used=ai_res.get("usage_metadata", {}).get("completion_tokens", 0),
            llm_raw_response=json.dumps(ai_res),
            execution_mode="HYBRID",
            ai_bypassed=False,
            bypass_reason="",
        )
        
        # Return AI response with updated status
        ai_res["status"] = status
        ai_res["rationale"] = rationale
        return ai_res

    except Exception as e:
        # FastAPI is down or returns invalid response -> Fallback behavior
        logger.error(f"AI Service invocation failed for {agent_id}: {str(e)}. Initiating fallback.")
        
        # Log AI offline Incident
        incident = SystemIncident.objects.create(
            incident_type=f"{agent_id}_SERVICE_OFFLINE",
            severity="HARD",
            agent_id=agent_id,
            affected_reference=input_reference,
            error_message=f"AI service failed: {str(e)}. Fallback activated.",
        )
        
        if cfg.fallback_behavior == "RULE_FALLBACK":
            # Safe Default: run rule-based fallback locally
            log_agent_action(
                agent_id=agent_id,
                agent_name=agent_name,
                input_reference=input_reference,
                input_payload=payload,
                output_payload=rule_out,
                confidence=rule_res.get("confidence", 0.0),
                status="SUCCESS",
                rationale=f"AI Service Offline Fallback: {str(e)}. Local rules executed successfully.",
                triggered_by=triggered_by,
                trigger_type=trigger_type,
                execution_mode="RULE_FALLBACK",
                ai_bypassed=True,
                bypass_reason=f"AI Service offline: {str(e)}. Fallback to rules.",
            )
            return rule_res
            
        elif cfg.fallback_behavior == "MANUAL_REVIEW":
            ref_model, ref_id = parse_reference(input_reference)
            ManualReviewCase.objects.get_or_create(
                reference_model=ref_model,
                reference_id=ref_id,
                agent_id=agent_id,
                defaults={
                    "manual_notes": f"AI service failed: {str(e)}. Manual review required.",
                    "incident": incident,
                    "status": "PENDING"
                }
            )
            log_agent_action(
                agent_id=agent_id,
                agent_name=agent_name,
                input_reference=input_reference,
                input_payload=payload,
                output_payload={},
                confidence=0.0,
                status="REQUIRES_HUMAN_REVIEW",
                rationale=f"AI service offline: {str(e)}. Policy fallback set to manual review.",
                triggered_by=triggered_by,
                trigger_type=trigger_type,
                execution_mode="RULE_FALLBACK",
                ai_bypassed=True,
                bypass_reason=f"AI Service offline: {str(e)}. Queue for manual review.",
            )
            return {
                "agent_id": agent_id,
                "agent_name": agent_name,
                "status": "REQUIRES_HUMAN_REVIEW",
                "confidence": 0.0,
                "rationale": f"AI service unreachable: {str(e)}. Scheduled for manual review.",
                "output": {}
            }
        else: # REJECT or default error raise
            raise RuntimeError(f"AI Service failed and fallback policy is set to REJECT. Error: {str(e)}")


def call_fastapi_agent(agent_id: str, payload: Dict, use_llm: bool = True) -> Dict:
    """
    Sends POST request to the corresponding agent endpoint on the FastAPI service.
    """
    endpoint_map = {
        "A1": "a1/validate-client",
        "A2": "a2/risk-score",
        "A3": "a3/recommendation",
        "A4": "a4/check-repayments",
        "A5": "a5/fraud-check",
        "A6": "a6/draft-message",
    }
    endpoint = endpoint_map.get(agent_id)
    if not endpoint:
        raise ValueError(f"Unknown endpoint for agent: {agent_id}")

    # Inject the override flag
    full_payload = {**payload, "use_llm": use_llm}

    response = httpx.post(
        f"{settings.AI_SERVICE_URL}/api/{endpoint}",
        json=full_payload,
        headers={"x-api-key": settings.AI_SERVICE_API_KEY},
        timeout=120.0
    )
    response.raise_for_status()
    return response.json()


def check_disagreement(agent_id: str, rule_out: Dict, ai_out: Dict) -> Tuple[bool, str]:
    """
    Checks if rule outputs and AI outputs diverge significantly.
    Returns (disagreed: bool, reason: str)
    """
    if not rule_out or not ai_out:
        return False, ""

    if agent_id == "A1":
        # Missing critical fields mismatch
        r_missing = set(rule_out.get("missing_critical_fields", []))
        a_missing = set(ai_out.get("missing_critical_fields", []))
        if r_missing != a_missing:
            return True, f"Missing fields mismatch. Rules: {list(r_missing)}, AI: {list(a_missing)}"
        
        # Data quality score mismatch > 15
        r_score = float(rule_out.get("data_quality_score", 0))
        a_score = float(ai_out.get("data_quality_score", 0))
        if abs(r_score - a_score) > 15:
            return True, f"KYC score mismatch by > 15. Rules: {r_score}, AI: {a_score}"

    elif agent_id == "A2":
        # Risk category mismatch (LOW/MEDIUM/HIGH)
        r_cat = rule_out.get("risk_category")
        a_cat = ai_out.get("risk_category")
        if r_cat != a_cat:
            return True, f"Risk category mismatch. Rules: {r_cat}, AI: {a_cat}"
        
        # Risk score mismatch > 15
        r_score = float(rule_out.get("risk_score", 0))
        a_score = float(ai_out.get("risk_score", 0))
        if abs(r_score - a_score) > 15:
            return True, f"Risk score mismatch by > 15. Rules: {r_score}, AI: {a_score}"

    elif agent_id == "A3":
        # Recommendation type mismatch
        r_rec = rule_out.get("recommendation_type")
        a_rec = ai_out.get("recommendation_type")
        if r_rec != a_rec:
            return True, f"Recommendation mismatch. Rules: {r_rec}, AI: {a_rec}"

    elif agent_id == "A5":
        # Fraud suspicious flag check
        r_susp = rule_out.get("is_suspicious")
        a_susp = ai_out.get("is_suspicious")
        if r_susp != a_susp:
            return True, f"Fraud suspicious mismatch. Rules: {r_susp}, AI: {a_susp}"

    return False, ""


def is_result_risky(agent_id: str, ai_out: Dict) -> bool:
    """
    Detects if the AI output contains high-risk indicators that require a review gate.
    """
    if not ai_out:
        return False

    if agent_id == "A2":
        # Risk category is High, or risk score is low (under 40)
        return ai_out.get("risk_category") == "HIGH" or float(ai_out.get("risk_score", 0)) < 40
    elif agent_id == "A3":
        # Rejection, Reduced loan amount, or Escalations are risky recommendations
        return ai_out.get("recommendation_type") in ["RECOMMEND_REJECTION", "RECOMMEND_ESCALATION", "RECOMMEND_REDUCED_AMOUNT"]
    elif agent_id == "A5":
        # Any suspicious fraud alert is risky
        return ai_out.get("is_suspicious") or float(ai_out.get("fraud_risk_score", 0)) >= 25

    return False


def parse_reference(input_reference: str) -> Tuple[str, int]:
    """
    Helper to parse 'loan:123' or 'client:45' into ('LoanApplication', 123).
    """
    try:
        parts = input_reference.split("|")
        # take the last or most specific one (e.g. loan:123)
        ref = parts[-1]
        model_key, id_str = ref.split(":")
        
        model_map = {
            "loan": "LoanApplication",
            "client": "Client",
            "comm": "NotificationQueue",
            "portfolio_scan": "RepaymentSchedule",
        }
        return model_map.get(model_key, "Unknown"), int(id_str)
    except Exception:
        return "Unknown", 0
