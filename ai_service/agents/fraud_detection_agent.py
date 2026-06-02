from .base_agent import BaseAgent
from typing import Dict, List


class FraudDetectionAgent(BaseAgent):
    """
    A5: Fraud Detection Agent
    Runs pattern-based fraud checks. Generates alerts and scores.
    CANNOT freeze accounts, blacklist clients, or take enforcement action.
    All enforcement requires Compliance Officer authorization.
    """

    def __init__(self):
        super().__init__(agent_id="A5", agent_name="Fraud Detection Agent")

    def run(self, input_data: Dict) -> Dict:
        check_type = input_data.get("check_type", "FULL")
        client_id = input_data.get("client_id")
        loan_id = input_data.get("loan_id")

        signals = []
        score = 0.0

        #IDENTITY CHECKS
        identity = input_data.get("identity_data", {})

        if identity.get("nic_duplicate_count", 0) > 0:
            signals.append({
                "type": "DUPLICATE_NIC",
                "detail": f"NIC appears in {identity['nic_duplicate_count']} other client records.",
                "weight": 40
            })
            score += 40

        if identity.get("phone_shared_count", 0) >= 3:
            signals.append({
                "type": "SHARED_PHONE",
                "detail": f"Phone number shared with {identity['phone_shared_count']} other clients.",
                "weight": 15
            })
            score += 15

        if identity.get("address_shared_count", 0) >= 3:
            signals.append({
                "type": "SHARED_ADDRESS",
                "detail": f"Home address shared with {identity['address_shared_count']} unrelated clients.",
                "weight": 10
            })
            score += 10

        # APPLICATION PATTERN CHECKS
        app_data = input_data.get("application_data", {})

        if app_data.get("applications_last_30_days", 0) >= 3:
            signals.append({
                "type": "RAPID_APPLICATIONS",
                "detail": f"{app_data['applications_last_30_days']} applications in last 30 days.",
                "weight": 20
            })
            score += 20

        requested_amount = float(app_data.get("requested_amount", 0))
        monthly_income = float(app_data.get("monthly_income", 0))
        annual_income = monthly_income * 12

        if annual_income > 0 and requested_amount > annual_income * 5:
            signals.append({
                "type": "UNUSUAL_AMOUNT",
                "detail": (
                    f"Requested LKR {requested_amount:,.0f} is more than 5× "
                    f"annual income ({annual_income:,.0f})."
                ),
                "weight": 20
            })
            score += 20

        # Check for suspiciously round amounts
        if requested_amount > 0 and requested_amount % 100000 == 0:
            signals.append({
                "type": "ROUND_AMOUNT_PATTERN",
                "detail": f"Loan amount LKR {requested_amount:,.0f} is an exact round number.",
                "weight": 5
            })
            score += 5

        # PAYMENT BEHAVIOR CHECKS 
        payment_data = input_data.get("payment_data", {})

        if payment_data.get("reversals_last_7_days", 0) >= 2:
            signals.append({
                "type": "PAYMENT_REVERSALS",
                "detail": f"{payment_data['reversals_last_7_days']} payment reversals in 7 days.",
                "weight": 25
            })
            score += 25

        # KYC ANOMALY 
        kyc_data = input_data.get("kyc_data", {})
        kyc_completion_minutes = kyc_data.get("completion_time_minutes", 999)

        if 0 < kyc_completion_minutes < 10:
            signals.append({
                "type": "KYC_RUSH",
                "detail": f"KYC completed in only {kyc_completion_minutes} minutes. Possible rubber-stamping.",
                "weight": 10
            })
            score += 10

        # Cap at 100
        score = min(100.0, score)

        # Determine severity
        if score >= 70:
            severity = "CRITICAL"
        elif score >= 50:
            severity = "HIGH"
        elif score >= 25:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        # Confidence is high — rule-based checks are deterministic
        confidence = 0.95 if signals else 0.90

        is_suspicious = score >= 25

        rationale = (
            f"Fraud Risk Score: {round(score, 1)}/100 — {severity}. "
            f"{len(signals)} signal(s) detected. "
            f"{'Investigation recommended.' if is_suspicious else 'No major fraud indicators.'}"
        )

        return self.build_response(
            output={
                "client_id": client_id,
                "loan_id": loan_id,
                "fraud_risk_score": round(score, 2),
                "severity": severity,
                "is_suspicious": is_suspicious,
                "signals": signals,
                "recommended_action": (
                    "OPEN_INVESTIGATION" if score >= 50
                    else "MONITOR" if score >= 25
                    else "CLEAR"
                ),
            },
            confidence=confidence,
            rationale=rationale,
            input_reference=f"client:{client_id}|loan:{loan_id}"
        )