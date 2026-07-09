# ai_service/agents/data_collection_agent.py
"""
A1 — Data Collection Agent
Validates KYC data completeness, consistency, and flags early fraud signals.
LLM upgrade: reasons about WHY data is suspicious, not just whether it's present.
"""

from .base_agent import BaseAgent
from typing import Dict
from decouple import config


from services.agent_config import get_agent_config

USE_LLM = config("A1_USE_LLM", default=False, cast=bool)


class DataCollectionAgent(BaseAgent):

    def __init__(self):
        super().__init__(agent_id="A1", agent_name="Data Collection Agent")

    def run(self, input_data: Dict) -> Dict:
        client_id  = input_data.get("client_id")
        client     = input_data.get("client_data", {})
        kyc        = input_data.get("kyc_data", {})

        cfg = get_agent_config("A1")
        if cfg["is_paused"]:
            return self.low_confidence_response(
                input_reference=f"client:{client_id}",
                reason=f"A1 is paused by admin: {cfg.get('pause_reason', 'No reason given')}"
            )

        use_llm = input_data.get("use_llm")
        if use_llm is None:
            use_llm = cfg["llm_enabled"]

        if use_llm:
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
        from services.nic_validator import validate_sri_lankan_nic
        from services.document_reader import read_nic_document
        from services.face_matcher import compare_faces

        # 1. NIC validation (pure Python)
        nic_check = validate_sri_lankan_nic(
            nic=client.get("nic_number", ""),
            form_dob=client.get("date_of_birth", ""),
            form_gender=client.get("gender", "")
        )

        # 2. Document OCR checks
        ocr_result = {}
        document_paths = kyc.get("document_paths", {})
        nic_front_path = document_paths.get("NIC_FRONT")
        if nic_front_path:
            ocr_result = read_nic_document(nic_front_path, client)

        # 3. Face matching checks
        face_result = {}
        selfie_path = document_paths.get("PHOTO")
        if nic_front_path and selfie_path:
            face_result = compare_faces(nic_front_path, selfie_path)

        # 4. Income consistency checks
        income_result = {}
        income_data = client.get("income", {})
        business_data = client.get("business", {})
        if income_data and business_data:
            SYSTEM_INCOME = """You are a Sri Lankan microfinance credit analyst.
Assess income plausibility only. Return valid JSON only, no other text."""
            
            # Stated details
            city = ""
            district = ""
            if client.get("addresses") and len(client.get("addresses")) > 0:
                addr = client.get("addresses")[0]
                city = addr.get("city", "")
                district = addr.get("district", "")
                
            USER_INCOME = f"""Assess this income profile for a microfinance applicant in Sri Lanka:
Occupation: {business_data.get('business_type', '')} — {business_data.get('business_name', '')}
Years operating: {business_data.get('years_in_operation', 0)}
Location: {city}, {district}
Monthly income claimed: LKR {income_data.get('monthly_income', 0)}
Monthly expenses: LKR {income_data.get('monthly_expenses', 0)}
Dependents: {income_data.get('number_of_dependents', 0)}

For context, typical monthly income ranges in Kalutara district:
- Rubber tapper: LKR 18,000–35,000
- Vegetable vendor: LKR 25,000–50,000
- Grocery shop: LKR 45,000–85,000
- Three-wheeler driver: LKR 40,000–70,000

Return ONLY this JSON structure:
{{
  "income_plausibility": "PLAUSIBLE" or "SUSPICIOUS" or "IMPLAUSIBLE",
  "concern_level": "NONE" or "LOW" or "HIGH",
  "flags": ["list any anomalies or high ratios"],
  "rationale": "one sentence explanation"
}}"""
            try:
                income_result, _ = call_llm(SYSTEM_INCOME, USER_INCOME, agent_id="A1")
            except Exception:
                pass

        # 5. Call main A1 LLM validation
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

        # Adjust score and flags based on NIC, OCR, Face Match, and Income checks
        score = float(output.get("data_quality_score", 100.0))
        consistency_flags = output.get("consistency_flags", [])
        fraud_signals = output.get("fraud_signals", [])

        # NIC Flags
        if not nic_check.get("valid_format", True):
            score -= 30
            fraud_signals.append("INVALID_NIC_FORMAT: NIC does not match Sri Lankan format rules.")
        elif nic_check.get("has_contradictions"):
            score -= 20
            for flag in nic_check.get("flags", []):
                fraud_signals.append(f"NIC: {flag}")

        # OCR Flags
        if ocr_result:
            if not ocr_result.get("document_readable"):
                score -= 10
                consistency_flags.append("OCR: NIC document is unreadable.")
            else:
                if ocr_result.get("name_match") is False:
                    score -= 25
                    fraud_signals.append(f"OCR: Name mismatch. Extracted '{ocr_result.get('extracted_name')}' from NIC.")
                if ocr_result.get("nic_match") is False:
                    score -= 30
                    fraud_signals.append(f"OCR: NIC mismatch. Extracted '{ocr_result.get('extracted_nic')}' from NIC.")
                if ocr_result.get("dob_match") is False:
                    score -= 20
                    fraud_signals.append(f"OCR: DOB mismatch. Extracted '{ocr_result.get('extracted_dob')}' from NIC.")
                if not ocr_result.get("document_appears_genuine", True):
                    score -= 20
                    fraud_signals.append("OCR: Document authenticity concerns.")
                for flag in ocr_result.get("flags", []):
                    consistency_flags.append(f"OCR: {flag}")

        # Face Match Flags
        if face_result.get("face_match_available"):
            if face_result.get("match_status") == "MISMATCH":
                score -= 20
                fraud_signals.append(face_result.get("flag", "Face mismatch detected."))
            elif face_result.get("match_status") == "UNCERTAIN":
                score -= 5
                consistency_flags.append(face_result.get("flag", "Face matching uncertain."))

        # Income Flags
        if income_result:
            concern = income_result.get("concern_level", "NONE")
            if concern == "HIGH":
                score -= 15
                fraud_signals.append(f"INCOME: {income_result.get('rationale', 'Suspicious income profile.')}")
            elif concern == "LOW":
                score -= 5
                consistency_flags.append(f"INCOME: {income_result.get('rationale', 'Minor income inconsistency.')}")
            for flag in income_result.get("flags", []):
                consistency_flags.append(f"INCOME: {flag}")

        # Clamp score between 0 and 100
        score = max(0.0, min(100.0, score))

        # Re-evaluate confidence if major flags are raised
        if fraud_signals:
            confidence = max(0.4, confidence - len(fraud_signals) * 0.1)

        # Decide recommendation (Verify, Review, or High Risk)
        # score >= 90 and zero flags -> RECOMMEND_VERIFY
        # score < 60 or major fraud signals -> HIGH_RISK_FLAG
        # otherwise -> REQUIRES_REVIEW
        if score >= 90.0 and len(fraud_signals) == 0 and len(consistency_flags) == 0:
            verification_recommendation = "RECOMMEND_VERIFY"
        elif score < 60.0 or len(fraud_signals) > 0:
            verification_recommendation = "HIGH_RISK_FLAG"
        else:
            verification_recommendation = "REQUIRES_REVIEW"

        # Low confidence -> flag for manual review
        if confidence_requires_manual_review(confidence):
            return self.low_confidence_response(
                input_reference=f"client:{client_id}",
                reason=f"LLM confidence {round(confidence, 2)} below threshold. Manual KYC review required."
            )

        # Build final response
        return self.build_response(
            output={
                "client_id":              client_id,
                "data_quality_score":     round(score, 2),
                "missing_critical_fields": output.get("missing_critical_fields", []),
                "consistency_flags":      consistency_flags,
                "fraud_signals":          fraud_signals,
                "nic_validation":         nic_check,
                "ocr_result":             ocr_result,
                "face_match":             face_result,
                "income_validation":      income_result,
                "verification_recommendation": verification_recommendation
            },
            confidence=round(confidence, 2),
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