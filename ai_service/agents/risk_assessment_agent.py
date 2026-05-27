from .base_agent import BaseAgent
from typing import Dict


class RiskAssessmentAgent(BaseAgent):
    """
    A2: Risk Assessment Agent
    Scores loan applications using rule-based analysis.
    Output must be reviewed by a Risk Analyst — A2 cannot approve or reject.
    """

    def __init__(self):
        super().__init__(agent_id="A2", agent_name="Risk Assessment Agent")

    def run(self, input_data: Dict) -> Dict:
        loan_id = input_data.get("loan_id")
        client = input_data.get("client_data", {})
        loan = input_data.get("loan_data", {})
        history = input_data.get("repayment_history", {})

        scores = {}
        signals = []

        # --- Factor 1: Debt-to-Income Ratio (25 pts) ---
        dti = float(loan.get("debt_to_income_ratio") or 0)
        if dti <= 0.30:
            scores["dti"] = 25.0
        elif dti <= 0.50:
            scores["dti"] = 15.0
        else:
            scores["dti"] = 0.0
            signals.append(f"High DTI ratio: {round(dti * 100, 1)}%")

        # --- Factor 2: Loan-to-Income Ratio (20 pts) ---
        monthly_income = float(client.get("monthly_income") or 0)
        loan_amount = float(loan.get("requested_amount") or 0)
        annual_income = monthly_income * 12

        if annual_income > 0:
            lti = loan_amount / annual_income
            if lti <= 2.0:
                scores["lti"] = 20.0
            elif lti <= 4.0:
                scores["lti"] = 10.0
            else:
                scores["lti"] = 0.0
                signals.append(f"Loan amount ({loan_amount}) is {round(lti, 1)}x annual income")
        else:
            scores["lti"] = 0.0
            signals.append("No income data — cannot calculate LTI")

        # --- Factor 3: KYC Completeness (15 pts) ---
        kyc_score = float(client.get("data_quality_score") or 0)
        scores["kyc"] = (kyc_score / 100) * 15

        # --- Factor 4: Income Stability (15 pts) ---
        years_in_operation = int(client.get("years_in_operation") or 0)
        if years_in_operation >= 3:
            scores["income_stability"] = 15.0
        elif years_in_operation >= 1:
            scores["income_stability"] = 8.0
        else:
            scores["income_stability"] = 3.0
            signals.append("Business less than 1 year old — income stability risk")

        # --- Factor 5: Previous Repayment History (15 pts) ---
        missed_payments = int(history.get("missed_payments") or 0)
        prev_loans = int(history.get("previous_loans_count") or 0)

        if prev_loans == 0:
            scores["repayment"] = 10.0  # No history — neutral score
        elif missed_payments == 0:
            scores["repayment"] = 15.0
        elif missed_payments <= 2:
            scores["repayment"] = 7.0
            signals.append(f"{missed_payments} missed payment(s) in history")
        else:
            scores["repayment"] = 0.0
            signals.append(f"Multiple missed payments: {missed_payments}")

        # --- Factor 6: Number of Dependents (10 pts) ---
        dependents = int(client.get("number_of_dependents") or 0)
        if dependents <= 2:
            scores["dependents"] = 10.0
        elif dependents <= 4:
            scores["dependents"] = 5.0
        else:
            scores["dependents"] = 2.0

        # --- Total Score ---
        total_score = sum(scores.values())
        total_score = max(0.0, min(100.0, total_score))

        # --- Risk Category ---
        if total_score >= 70:
            risk_category = "LOW"
        elif total_score >= 40:
            risk_category = "MEDIUM"
        else:
            risk_category = "HIGH"
            signals.append("HIGH risk classification — Branch Manager review required")

        # --- Confidence ---
        # Confidence is lower if income data is missing or history is absent
        confidence = 0.9
        if monthly_income == 0:
            confidence -= 0.3
        if prev_loans == 0:
            confidence -= 0.1
        confidence = max(0.3, confidence)

        # Low confidence → flag for human review
        if confidence < 0.5:
            return self.low_confidence_response(
                input_reference=f"loan:{loan_id}",
                reason="Insufficient data for reliable risk scoring. Human review required."
            )

        # --- Rationale Text ---
        rationale = (
            f"Risk Score: {round(total_score, 1)}/100 — Category: {risk_category}. "
            f"DTI={round(dti * 100, 1)}%, LTI={round(lti if annual_income > 0 else 0, 2)}x, "
            f"KYC={round(kyc_score, 1)}%, "
            f"Business age={years_in_operation}yr(s), "
            f"Missed payments={missed_payments}. "
        )
        if signals:
            rationale += f"Signals: {'; '.join(signals)}."

        return self.build_response(
            output={
                "loan_id": loan_id,
                "risk_score": round(total_score, 2),
                "risk_category": risk_category,
                "factor_scores": {
                    "dti_score": scores["dti"],
                    "lti_score": scores["lti"],
                    "kyc_score": round(scores["kyc"], 2),
                    "income_stability_score": scores["income_stability"],
                    "repayment_history_score": scores["repayment"],
                    "dependents_score": scores["dependents"],
                },
                "default_signals": signals,
                "required_action": (
                    "LOAN_OFFICER_REVIEW" if risk_category == "LOW"
                    else "RISK_ANALYST_REQUIRED" if risk_category == "MEDIUM"
                    else "BRANCH_MANAGER_ESCALATION"
                )
            },
            confidence=round(confidence, 2),
            rationale=rationale,
            input_reference=f"loan:{loan_id}"
        )