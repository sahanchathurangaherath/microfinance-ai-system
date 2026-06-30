
"""
A3 — Recommendation Agent
Reads A2 risk output and generates an explainable recommendation.
LLM upgrade: the local model reads A2's full rationale text — not just the score number.
A3 NEVER approves or rejects — only recommends. Human has final authority.
"""

from .base_agent import BaseAgent
from typing import Dict
from decouple import config


USE_LLM = config("A3_USE_LLM", default=False, cast=bool)


class RecommendationAgent(BaseAgent):

    def __init__(self):
        super().__init__(agent_id="A3", agent_name="Recommendation Agent")

    def run(self, input_data: Dict) -> Dict:
        if USE_LLM:
            return self._llm_recommend(input_data)
        else:
            return self._rule_recommend(input_data)

   
    # LLM PATH
    

    def _llm_recommend(self, input_data: Dict) -> Dict:
        """
        LLM-powered recommendation.
        Key advantage over rule-based: the local LLM reads A2's full ai_rationale text,
        not just the score number — enabling genuine multi-step reasoning.
        Uses few-shot examples from recommendation_examples.json if available.
        """
        import json
        import os
        from services.llm_client import call_llm
        from services.guardrails import validate_a3_output, confidence_requires_manual_review

        loan_id          = input_data.get("loan_id")
        risk_score       = float(input_data.get("risk_score") or 0)
        risk_category    = input_data.get("risk_category", "HIGH")
        a2_rationale     = input_data.get("ai_rationale", "")   # A2's full reasoning
        signals          = input_data.get("default_signals", [])
        kyc_score        = float(input_data.get("kyc_score") or 0)
        requested_amount = float(input_data.get("requested_amount") or 0)
        monthly_income   = float(input_data.get("monthly_income") or 0)
        duration_months  = int(input_data.get("requested_duration_months") or 12)
        dti              = float(input_data.get("debt_to_income_ratio") or 0)

        # Load few-shot examples if available
        few_shot_text = ""
        examples_path = os.path.join(
            os.path.dirname(__file__), "data", "recommendation_examples.json"
        )
        if os.path.exists(examples_path):
            try:
                with open(examples_path, "r") as f:
                    examples = json.load(f)
                if examples:
                    few_shot_text = "\n\nPAST DECISION EXAMPLES:\n" + json.dumps(examples[:5], indent=2)
            except json.JSONDecodeError:
                few_shot_text = ""

        SYSTEM_PROMPT = """You are a Loan Recommendation Assistant for a microfinance institution in Sri Lanka.
You assist officers — you do NOT approve or reject loans. Your output is advisory only.
The Credit Committee and Branch Manager will make all final decisions.
Always respond with valid JSON only. No extra text, no markdown."""

        USER_PROMPT = f"""Generate a loan recommendation based on the risk analysis below.

A2 RISK ANALYSIS (full reasoning):
{a2_rationale if a2_rationale else "No rationale provided — use numeric scores only."}

RISK SCORE: {risk_score}/100
RISK CATEGORY: {risk_category}
RISK SIGNALS: {json.dumps(signals)}

LOAN DETAILS:
- Requested Amount: LKR {requested_amount:,.2f}
- Duration: {duration_months} months
- Client Monthly Income: LKR {monthly_income:,.2f}
- Debt-to-Income Ratio: {round(dti * 100, 1)}%
- KYC Completeness Score: {kyc_score}/100
{few_shot_text}

Choose ONE recommendation type:
- RECOMMEND_APPROVAL        — score high, income stable, KYC complete
- RECOMMEND_REJECTION       — score critically low, multiple serious signals
- RECOMMEND_REDUCED_AMOUNT  — score acceptable but amount exceeds affordability
- RECOMMEND_MORE_DOCUMENTS  — KYC score below 60 or income unverified
- RECOMMEND_ESCALATION      — borderline HIGH risk, needs senior review

Return ONLY this JSON:
{{
  "recommendation_type": "<one of the 5 types above>",
  "recommended_amount": <float or null if not reducing>,
  "recommended_duration_months": <int, same as requested unless reducing>,
  "explanation": "<2-3 sentence plain English explanation for the officer>",
  "reasons": ["reason 1", "reason 2", "reason 3"],
  "alternative_product_suggestion": "<string or null>",
  "confidence": <float 0.0-1.0>
}}"""

        try:
            output, _ = call_llm(SYSTEM_PROMPT, USER_PROMPT, agent_id=self.agent_id)
        except Exception as e:
            return self.low_confidence_response(
                input_reference=f"loan:{loan_id}",
                reason=f"LLM service error: {str(e)}. Manual recommendation review required."
            )

        is_valid, reason = validate_a3_output(output)
        if not is_valid:
            return self.low_confidence_response(
                input_reference=f"loan:{loan_id}",
                reason=f"LLM output failed validation: {reason}. Manual review required."
            )

        confidence = float(output["confidence"])

        if confidence_requires_manual_review(confidence):
            return self.low_confidence_response(
                input_reference=f"loan:{loan_id}",
                reason=f"LLM confidence {round(confidence, 2)} below threshold. Branch Manager review required."
            )

        return self.build_response(
            output={
                "loan_id":                    loan_id,
                "recommendation_type":        output["recommendation_type"],
                "recommended_amount":         output.get("recommended_amount"),
                "recommended_duration_months": output.get("recommended_duration_months", duration_months),
                "explanation":                output["explanation"],
                "reasons":                    output.get("reasons", []),
                "alternative_product_suggestion": output.get("alternative_product_suggestion"),
            },
            confidence=confidence,
            rationale=output["explanation"],
            input_reference=f"loan:{loan_id}"
        )

  
    # RULE-BASED PATH (original MVP logic — preserved as fallback)
    

    def _rule_recommend(self, input_data: Dict) -> Dict:
        """
        Original MVP rule-based recommendation.
        Active when A3_USE_LLM=false in .env
        """
        loan_id          = input_data.get("loan_id")
        risk_score       = float(input_data.get("risk_score") or 0)
        risk_category    = input_data.get("risk_category", "HIGH")
        signals          = input_data.get("default_signals", [])
        kyc_score        = float(input_data.get("kyc_score") or 0)
        requested_amount = float(input_data.get("requested_amount") or 0)
        monthly_income   = float(input_data.get("monthly_income") or 0)
        duration_months  = int(input_data.get("requested_duration_months") or 12)
        dti              = float(input_data.get("debt_to_income_ratio") or 0)

        reasons = []
        recommendation = None
        recommended_amount = None

        if kyc_score < 60:
            recommendation = "RECOMMEND_MORE_DOCUMENTS"
            reasons.append(f"KYC score only {round(kyc_score, 1)}% — documents incomplete.")
            reasons.append("Key documents may be missing or unverified.")

        elif risk_category == "HIGH" and risk_score < 30:
            recommendation = "RECOMMEND_REJECTION"
            reasons.append(f"Risk score {round(risk_score, 1)}/100 is critically low.")
            reasons.append("Multiple default risk signals detected.")
            for s in signals[:3]:
                reasons.append(f"Signal: {s}")

        elif risk_category == "HIGH" and risk_score >= 30:
            recommendation = "RECOMMEND_ESCALATION"
            reasons.append(f"Risk score {round(risk_score, 1)}/100 — HIGH category.")
            reasons.append("Branch Manager assessment required before proceeding.")

        elif risk_category == "MEDIUM" and dti > 0.40:
            max_monthly = monthly_income * 0.30
            recommended_amount = round(max_monthly * duration_months * 0.85, 2)
            recommended_amount = min(recommended_amount, requested_amount * 0.70)
            recommendation = "RECOMMEND_REDUCED_AMOUNT"
            reasons.append(f"DTI is {round(dti*100,1)}% — exceeds 40% threshold.")
            reasons.append(f"Suggested reduced amount: LKR {recommended_amount:,.2f}")

        elif risk_category in ["LOW", "MEDIUM"] and risk_score >= 50:
            recommendation = "RECOMMEND_APPROVAL"
            reasons.append(f"Risk score {round(risk_score, 1)}/100 — {risk_category} category.")
            reasons.append("Client meets minimum lending criteria.")
            reasons.append("Officer authorization still required.")

        else:
            recommendation = "RECOMMEND_ESCALATION"
            reasons.append("Insufficient confidence for a clear recommendation.")
            reasons.append("Branch Manager review advised.")

        confidence_map = {
            "RECOMMEND_APPROVAL": 0.85,
            "RECOMMEND_REJECTION": 0.90,
            "RECOMMEND_REDUCED_AMOUNT": 0.75,
            "RECOMMEND_MORE_DOCUMENTS": 0.95,
            "RECOMMEND_ESCALATION": 0.70,
        }
        confidence = confidence_map.get(recommendation, 0.70)
        if not input_data.get("has_repayment_history", False):
            confidence -= 0.05

        explanation = (
            f"A3 recommendation: {recommendation}. "
            f"Risk score {round(risk_score,1)}/100 ({risk_category}). "
            f"Key reasons: {'; '.join(reasons[:2])}. "
            "NOTE: AI recommendations are advisory only. Human approval is mandatory."
        )

        return self.build_response(
            output={
                "loan_id":                    loan_id,
                "recommendation_type":        recommendation,
                "recommended_amount":         recommended_amount,
                "recommended_duration_months": duration_months,
                "explanation":                explanation,
                "reasons":                    reasons,
                "alternative_product_suggestion": None,
            },
            confidence=round(confidence, 2),
            rationale=explanation,
            input_reference=f"loan:{loan_id}"
        )