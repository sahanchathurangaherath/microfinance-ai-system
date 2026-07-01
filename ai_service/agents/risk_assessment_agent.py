
"""
A2 — Risk Assessment Agent
Scores loan applications using multi-factor analysis.
Output must be reviewed by a Risk Analyst — A2 cannot approve or reject.
"""

from .base_agent import BaseAgent
from typing import Dict
from decouple import config


USE_LLM = config("A2_USE_LLM", default=False, cast=bool)


class RiskAssessmentAgent(BaseAgent):

    def __init__(self):
        super().__init__(agent_id="A2", agent_name="Risk Assessment Agent")

    def run(self, input_data: Dict) -> Dict:
        if USE_LLM:
            return self._llm_score(input_data)
        else:
            return self._rule_score(input_data)

    
    # LLM PATH
    

    def _llm_score(self, input_data: Dict) -> Dict:
        """
        LLM-powered risk scoring.
        The local model reasons through all 6 factors and provides full rationale.
        Returns the same output structure as _rule_score so Django needs no changes.
        """
        import json
        from services.llm_client import call_llm
        from services.guardrails import validate_a2_output, confidence_requires_manual_review

        loan_id = input_data.get("loan_id")
        client  = input_data.get("client_data", {})
        loan    = input_data.get("loan_data", {})
        history = input_data.get("repayment_history", {})

        SYSTEM_PROMPT = """You are a Credit Risk Analyst for a microfinance institution in Sri Lanka.
You evaluate loan applications for creditworthiness using financial data.
You SCORE and CLASSIFY risk — you do NOT approve or reject loans.
The Risk Analyst officer will review your output before any decision is made.
Always respond with valid JSON only. No extra text, no markdown."""

        USER_PROMPT = f"""Evaluate this loan application for credit risk.

LOAN APPLICATION:
- Loan ID: {loan_id}
- Requested Amount: LKR {loan.get("requested_amount", 0)}
- Duration: {loan.get("requested_duration_months", 0)} months
- Debt-to-Income Ratio: {loan.get("debt_to_income_ratio", "unknown")}

CLIENT FINANCIAL PROFILE:
- Monthly Income: LKR {client.get("monthly_income", 0)}
- Number of Dependents: {client.get("number_of_dependents", 0)}
- KYC Data Quality Score: {client.get("data_quality_score", 0)}/100
- Years in Business/Employment: {client.get("years_in_operation", 0)}

REPAYMENT HISTORY:
- Previous Loans Count: {history.get("previous_loans_count", 0)}
- Missed Payments: {history.get("missed_payments", 0)}

Assess all 6 factors: DTI ratio, Loan-to-Income ratio, KYC completeness,
income stability, repayment history, number of dependents.

Return ONLY this JSON:
{{
  "risk_score": <float 0-100, where 0=highest risk, 100=lowest risk>,
  "risk_category": "LOW" or "MEDIUM" or "HIGH",
  "confidence": <float 0.0-1.0>,
  "factor_scores": {{
    "dti_score":               <float, max 25>,
    "lti_score":               <float, max 20>,
    "kyc_score":               <float, max 15>,
    "income_stability_score":  <float, max 15>,
    "repayment_history_score": <float, max 15>,
    "dependents_score":        <float, max 10>
  }},
  "default_signals": ["list of specific risk warning signals, empty if none"],
  "required_action": "LOAN_OFFICER_REVIEW" or "RISK_ANALYST_REQUIRED" or "BRANCH_MANAGER_ESCALATION",
  "ai_rationale": "<step-by-step reasoning for the Risk Analyst covering all 6 factors>"
}}

Risk Category rules:
- Score 70-100 → LOW → required_action: LOAN_OFFICER_REVIEW
- Score 40-69  → MEDIUM → required_action: RISK_ANALYST_REQUIRED
- Score 0-39   → HIGH   → required_action: BRANCH_MANAGER_ESCALATION"""

        try:
            output, usage = call_llm(SYSTEM_PROMPT, USER_PROMPT, agent_id=self.agent_id)
        except Exception as e:
            return self.low_confidence_response(
                input_reference=f"loan:{loan_id}",
                reason=f"LLM service error: {str(e)}. Manual risk review required."
            )

        # Validate structure
        is_valid, reason = validate_a2_output(output)
        if not is_valid:
            return self.low_confidence_response(
                input_reference=f"loan:{loan_id}",
                reason=f"LLM output failed validation: {reason}. Manual review required."
            )

        confidence = float(output["confidence"])

        if confidence_requires_manual_review(confidence):
            return self.low_confidence_response(
                input_reference=f"loan:{loan_id}",
                reason=f"LLM confidence {round(confidence, 2)} below threshold. Risk Analyst manual review required."
            )

        factor_scores = output.get("factor_scores", {})

        return self.build_response(
            output={
                "loan_id":          loan_id,
                "risk_score":       round(float(output["risk_score"]), 2),
                "risk_category":    output["risk_category"],
                "factor_scores":    {
                    "dti_score":               float(factor_scores.get("dti_score", 0)),
                    "lti_score":               float(factor_scores.get("lti_score", 0)),
                    "kyc_score":               float(factor_scores.get("kyc_score", 0)),
                    "income_stability_score":  float(factor_scores.get("income_stability_score", 0)),
                    "repayment_history_score": float(factor_scores.get("repayment_history_score", 0)),
                    "dependents_score":        float(factor_scores.get("dependents_score", 0)),
                },
                "default_signals":  output.get("default_signals", []),
                "required_action":  output.get("required_action", "RISK_ANALYST_REQUIRED"),
            },
            confidence=confidence,
            rationale=output.get("ai_rationale", ""),
            input_reference=f"loan:{loan_id}",
            usage_metadata=usage
        )

    
    # RULE-BASED PATH 
   
    def _rule_score(self, input_data: Dict) -> Dict:
        """
        Original MVP 6-factor rule-based scoring.
        Active when A2_USE_LLM=false in .env
        """
        loan_id = input_data.get("loan_id")
        client  = input_data.get("client_data", {})
        loan    = input_data.get("loan_data", {})
        history = input_data.get("repayment_history", {})

        scores  = {}
        signals = []

        # Factor 1: DTI (25 pts)
        dti = float(loan.get("debt_to_income_ratio") or 0)
        if dti <= 0.30:   scores["dti"] = 25.0
        elif dti <= 0.50: scores["dti"] = 15.0
        else:
            scores["dti"] = 0.0
            signals.append(f"High DTI ratio: {round(dti * 100, 1)}%")

        # Factor 2: LTI (20 pts)
        monthly_income = float(client.get("monthly_income") or 0)
        loan_amount    = float(loan.get("requested_amount") or 0)
        annual_income  = monthly_income * 12
        lti = 0.0
        if annual_income > 0:
            lti = loan_amount / annual_income
            if lti <= 2.0:   scores["lti"] = 20.0
            elif lti <= 4.0: scores["lti"] = 10.0
            else:
                scores["lti"] = 0.0
                signals.append(f"Loan is {round(lti, 1)}x annual income")
        else:
            scores["lti"] = 0.0
            signals.append("No income data — cannot calculate LTI")

        # Factor 3: KYC completeness (15 pts)
        kyc_quality    = float(client.get("data_quality_score") or 0)
        scores["kyc"]  = (kyc_quality / 100) * 15

        # Factor 4: Income stability (15 pts)
        years = int(client.get("years_in_operation") or 0)
        if years >= 3:   scores["income_stability"] = 15.0
        elif years >= 1: scores["income_stability"] = 8.0
        else:
            scores["income_stability"] = 3.0
            signals.append("Business less than 1 year — income stability risk")

        # Factor 5: Repayment history (15 pts)
        missed   = int(history.get("missed_payments") or 0)
        prev_cnt = int(history.get("previous_loans_count") or 0)
        if prev_cnt == 0:   scores["repayment"] = 10.0
        elif missed == 0:   scores["repayment"] = 15.0
        elif missed <= 2:
            scores["repayment"] = 7.0
            signals.append(f"{missed} missed payment(s) on record")
        else:
            scores["repayment"] = 0.0
            signals.append(f"Multiple missed payments: {missed}")

        # Factor 6: Dependents (10 pts)
        deps = int(client.get("number_of_dependents") or 0)
        if deps <= 2:   scores["dependents"] = 10.0
        elif deps <= 4: scores["dependents"] = 5.0
        else:           scores["dependents"] = 2.0

        total_score   = max(0.0, min(100.0, sum(scores.values())))
        risk_category = "LOW" if total_score >= 70 else ("MEDIUM" if total_score >= 40 else "HIGH")

        if risk_category == "HIGH":
            signals.append("HIGH risk — Branch Manager review required")

        confidence = 0.9
        if monthly_income == 0: confidence -= 0.3
        if prev_cnt == 0:       confidence -= 0.1
        confidence = max(0.3, confidence)

        if confidence < 0.5:
            return self.low_confidence_response(
                input_reference=f"loan:{loan_id}",
                reason="Insufficient data for reliable risk scoring."
            )

        rationale = (
            f"Risk Score: {round(total_score, 1)}/100 — {risk_category}. "
            f"DTI={round(dti*100,1)}%, LTI={round(lti,2)}x, "
            f"KYC={round(kyc_quality,1)}%, "
            f"Business age={years}yr(s), Missed payments={missed}. "
            + (f"Signals: {'; '.join(signals)}." if signals else "No signals.")
        )

        required_action = (
            "LOAN_OFFICER_REVIEW"       if risk_category == "LOW"
            else "RISK_ANALYST_REQUIRED" if risk_category == "MEDIUM"
            else "BRANCH_MANAGER_ESCALATION"
        )

        return self.build_response(
            output={
                "loan_id":       loan_id,
                "risk_score":    round(total_score, 2),
                "risk_category": risk_category,
                "factor_scores": {
                    "dti_score":               scores["dti"],
                    "lti_score":               scores["lti"],
                    "kyc_score":               round(scores["kyc"], 2),
                    "income_stability_score":  scores["income_stability"],
                    "repayment_history_score": scores["repayment"],
                    "dependents_score":        scores["dependents"],
                },
                "default_signals":  signals,
                "required_action":  required_action,
            },
            confidence=round(confidence, 2),
            rationale=rationale,
            input_reference=f"loan:{loan_id}"
        )