# ai_service/agents/data_collection_agent.py
"""
A1 — Data Collection Agent
Validates KYC data completeness, consistency, and flags early fraud signals.
LLM upgrade: reasons about WHY data is suspicious, not just whether it's present.
"""

from .base_agent import BaseAgent
from typing import Dict
from decouple import config


USE_LLM = config("A1_USE_LLM", default=False, cast=bool)


class DataCollectionAgent(BaseAgent):

    def __init__(self):
        super().__init__(agent_id="A1", agent_name="Data Collection Agent")

    def run(self, input_data: Dict) -> Dict:
        client_id  = input_data.get("client_id")
        client     = input_data.get("client_data", {})
        kyc        = input_data.get("kyc_data", {})

        if USE_LLM:
            return self._llm_validate(client_id, client, kyc)
        else:
            return self._rule_validate(client_id, client, kyc)

   
    # LLM PATH


    def _llm_validate(self, client_id, client: Dict, kyc: Dict) -> Dict:
        """
        LLM-powered KYC validation.
        LLM reasons about completeness, consistency, and fraud signals.
        """
        import json
        from services.llm_client import call_llm
        from services.guardrails import validate_a1_output, confidence_requires_manual_review

        SYSTEM_PROMPT = """You are a KYC Data Quality Analyst for a microfinance institution in Sri Lanka.
Your job is to evaluate client data for completeness, internal consistency, and early fraud signals.
You ASSIST the Loan Officer — you do NOT approve or reject the client.
Always respond with valid JSON only. No extra text."""

        USER_PROMPT = f"""Evaluate this client's KYC data:

CLIENT DATA:
{json.dumps(client, indent=2, default=str)}

KYC CHECKLIST DATA:
{json.dumps(kyc, indent=2, default=str)}

Return ONLY this JSON structure:
{{
  "data_quality_score": <float 0-100, overall data completeness and quality>,
  "missing_critical_fields": ["list of field names that are missing or empty"],
  "consistency_flags": ["list of any inconsistencies found, e.g. income vs business age mismatch"],
  "fraud_signals": ["list of any early warning fraud signals, empty list if none"],
  "confidence": <float 0.0-1.0, your confidence in this assessment>,
  "rationale": "<2-3 sentence plain English explanation for the Loan Officer>"
}}"""

        try:
            output, usage = call_llm(SYSTEM_PROMPT, USER_PROMPT, agent_id=self.agent_id)
        except Exception as e:
            # Local LLM failed — return low confidence to trigger Manual Mode
            return self.low_confidence_response(
                input_reference=f"client:{client_id}",
                reason=f"LLM service error: {str(e)}. Manual KYC review required."
            )

        # Validate output structure
        is_valid, reason = validate_a1_output(output)
        if not is_valid:
            return self.low_confidence_response(
                input_reference=f"client:{client_id}",
                reason=f"LLM output failed validation: {reason}. Manual review required."
            )

        confidence = float(output.get("confidence", 0.5))

        # Low confidence → flag for manual review
        if confidence_requires_manual_review(confidence):
            return self.low_confidence_response(
                input_reference=f"client:{client_id}",
                reason=f"LLM confidence {round(confidence, 2)} below threshold. Manual KYC review required."
            )

        return self.build_response(
            output={
                "client_id":              client_id,
                "data_quality_score":     float(output["data_quality_score"]),
                "missing_critical_fields": output.get("missing_critical_fields", []),
                "consistency_flags":      output.get("consistency_flags", []),
                "fraud_signals":          output.get("fraud_signals", []),
            },
            confidence=confidence,
            rationale=output.get("rationale", ""),
            input_reference=f"client:{client_id}",
            usage_metadata=usage
        )

    
    # RULE-BASED PATH 

    def _rule_validate(self, client_id, client: Dict, kyc: Dict) -> Dict:
        """
        Original MVP rule-based scoring.
        Active when A1_USE_LLM=false in .env
        """
        score = 0.0
        missing = []
        signals = []

        # Identity fields
        if client.get("nic_number"):        score += 15
        else:                               missing.append("nic_number")
        if client.get("first_name"):        score += 5
        else:                               missing.append("first_name")
        if client.get("last_name"):         score += 5
        else:                               missing.append("last_name")
        if client.get("date_of_birth"):     score += 5
        else:                               missing.append("date_of_birth")

        # Contact fields
        if client.get("phone_primary"):     score += 5
        else:                               missing.append("phone_primary")

        # KYC checklist fields
        if kyc.get("address_verified"):     score += 10
        else:                               missing.append("address_verified")
        if kyc.get("income_verified"):      score += 15
        else:                               missing.append("income_verified")
        if kyc.get("id_document_uploaded"): score += 15
        else:                               missing.append("id_document_uploaded")
        if kyc.get("income_document_uploaded"): score += 15
        else:                               missing.append("income_document_uploaded")

        # Business info
        if client.get("monthly_income"):    score += 10
        else:                               missing.append("monthly_income"); signals.append("Income data missing")

        score = min(100.0, score)

        confidence = 0.85 if not missing else max(0.4, 0.85 - len(missing) * 0.05)

        rationale = (
            f"Data quality score: {round(score, 1)}/100. "
            f"Missing fields: {', '.join(missing) if missing else 'None'}. "
            f"Signals: {', '.join(signals) if signals else 'None'}."
        )

        if confidence < 0.5:
            return self.low_confidence_response(
                input_reference=f"client:{client_id}",
                reason="Too many missing fields for reliable assessment."
            )

        return self.build_response(
            output={
                "client_id":               client_id,
                "data_quality_score":      round(score, 2),
                "missing_critical_fields": missing,
                "consistency_flags":       [],
                "fraud_signals":           signals,
            },
            confidence=round(confidence, 2),
            rationale=rationale,
            input_reference=f"client:{client_id}"
        )