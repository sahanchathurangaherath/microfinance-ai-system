MIN_CONFIDENCE = 0.30

VALID_RISK_CATEGORIES      = {"LOW", "MEDIUM", "HIGH"}
VALID_RECOMMENDATION_TYPES = {
    "RECOMMEND_APPROVAL", "RECOMMEND_REJECTION", "RECOMMEND_REDUCED_AMOUNT",
    "RECOMMEND_MORE_DOCUMENTS", "RECOMMEND_ESCALATION",
}
VALID_FRAUD_SEVERITIES     = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
VALID_BEHAVIORAL_PATTERNS  = {
    "CONSISTENT_PAYER", "EARLY_DETERIORATION", "SEASONAL_STRESS",
    "RECOVERING", "CHRONIC_LATE", "FIRST_DEFAULT", "UNKNOWN",
}
_PROHIBITED_FRAUD_WORDS    = ["freeze", "block", "suspend", "blacklist", "arrest"]
_PROHIBITED_MESSAGE_WORDS  = ["legal action", "court", "arrest", "police", "blacklist"]


def confidence_requires_manual_review(confidence: float) -> bool:
    return float(confidence) < MIN_CONFIDENCE


def validate_a1_output(output: dict) -> tuple[bool, str]:
    score = output.get("data_quality_score")
    if score is None or not (0 <= float(score) <= 100):
        return False, "data_quality_score out of 0–100 range"
    if "rationale" not in output or not output["rationale"]:
        return False, "rationale is required"
    return True, ""


def validate_a2_output(output: dict) -> tuple[bool, str]:
    score = output.get("risk_score")
    if score is None or not (0 <= float(score) <= 100):
        return False, "risk_score out of 0–100 range"
    if output.get("risk_category") not in VALID_RISK_CATEGORIES:
        return False, "risk_category must be LOW, MEDIUM, or HIGH"
    conf = output.get("confidence")
    if conf is None or not (0 <= float(conf) <= 1):
        return False, "confidence out of 0–1 range"
    if not output.get("ai_rationale"):
        return False, "ai_rationale is required"
    return True, ""


def validate_a4_llm_output(output: dict) -> tuple[bool, str]:
    prob = output.get("predicted_default_probability")
    if prob is None or not (0 <= float(prob) <= 1):
        return False, "predicted_default_probability out of 0–1 range"
    if output.get("behavioral_pattern_label") not in VALID_BEHAVIORAL_PATTERNS:
        return False, "behavioral_pattern_label is invalid"
    return True, ""


def validate_a5_output(output: dict) -> tuple[bool, str]:
    score = output.get("fraud_risk_score")
    if score is None or not (0 <= float(score) <= 100):
        return False, "fraud_risk_score out of 0–100 range"
    if output.get("severity") not in VALID_FRAUD_SEVERITIES:
        return False, "severity is invalid"
    rationale = output.get("verdict_rationale", "").lower()
    for word in _PROHIBITED_FRAUD_WORDS:
        if word in rationale:
            return False, f"Prohibited enforcement word '{word}' in output"
    return True, ""


def validate_a3_output(output: dict) -> tuple[bool, str]:
    if output.get("recommendation_type") not in VALID_RECOMMENDATION_TYPES:
        return False, f"recommendation_type '{output.get('recommendation_type')}' is invalid"
    if not output.get("explanation"):
        return False, "explanation is required"
    return True, ""


def validate_a6_output(output: dict) -> tuple[bool, str]:
    """Validate A6 LLM message drafts."""
    drafts = output.get("drafts", [])
    if not drafts or not isinstance(drafts, list):
        return False, "drafts list is required and must not be empty"

    for draft in drafts:
        body = draft.get("body", "").lower()
        for word in _PROHIBITED_MESSAGE_WORDS:
            if word in body:
                return False, f"Prohibited language '{word}' found in message draft"
        if not draft.get("body"):
            return False, "draft body cannot be empty"

    return True, ""