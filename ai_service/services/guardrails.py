# ai_service/services/guardrails.py
"""
Output validators for every LLM agent.
If validation fails, the caller triggers Manual Mode — agents never guess.
"""

VALID_RISK_CATEGORIES = {"LOW", "MEDIUM", "HIGH"}
MIN_CONFIDENCE        = 0.65   # Below this → ManualReviewCase in Django


def validate_a1_output(output: dict) -> tuple[bool, str]:
    """Validate A1 KYC data quality output."""
    score = output.get("data_quality_score")
    if score is None or not (0 <= float(score) <= 100):
        return False, "data_quality_score missing or out of 0–100 range"
    if "missing_critical_fields" not in output:
        return False, "missing_critical_fields list is required"
    if "rationale" not in output or not output["rationale"]:
        return False, "rationale string is required"
    return True, ""


def validate_a2_output(output: dict) -> tuple[bool, str]:
    """Validate A2 risk assessment output."""
    score = output.get("risk_score")
    if score is None or not (0 <= float(score) <= 100):
        return False, "risk_score missing or out of 0–100 range"
    if output.get("risk_category") not in VALID_RISK_CATEGORIES:
        return False, f"risk_category must be LOW, MEDIUM, or HIGH"
    confidence = output.get("confidence")
    if confidence is None or not (0 <= float(confidence) <= 1):
        return False, "confidence missing or out of 0–1 range"
    if "ai_rationale" not in output or not output["ai_rationale"]:
        return False, "ai_rationale string is required"
    return True, ""


def confidence_requires_manual_review(confidence: float) -> bool:
    """Returns True if the confidence is too low to proceed automatically."""
    return float(confidence) < MIN_CONFIDENCE