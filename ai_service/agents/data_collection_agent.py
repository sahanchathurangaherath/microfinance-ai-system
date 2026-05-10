from .base_agent import BaseAgent
from typing import Dict


class DataCollectionAgent(BaseAgent):
    """
    A1: Data Collection Agent
    Validates client profile completeness and generates a data quality score.
    Does NOT approve or reject clients — only scores and flags missing data.
    """

    def __init__(self):
        super().__init__(agent_id="A1", agent_name="Data Collection Agent")

    def run(self, input_data: Dict) -> Dict:
        client_id = input_data.get("client_id")
        client = input_data.get("client_data", {})
        kyc = input_data.get("kyc_data", {})

        issues = []
        score = 100.0

        # Required field checks
        required_fields = ['nic_number', 'first_name', 'last_name', 'date_of_birth',
                           'gender', 'phone_primary']
        for field in required_fields:
            if not client.get(field):
                issues.append(f"Missing required field: {field}")
                score -= 10

        # Income check 
        income = client.get("income", {})
        if not income:
            issues.append("No income information provided")
            score -= 15
        else:
            if not income.get("monthly_income") or float(income.get("monthly_income", 0)) <= 0:
                issues.append("Monthly income is zero or missing")
                score -= 10

        # --- Address check ---
        addresses = client.get("addresses", [])
        if not addresses:
            issues.append("No address information provided")
            score -= 10

        # --- KYC document checks ---
        if not kyc.get("nic_verified"):
            issues.append("NIC not verified")
            score -= 10

        if not kyc.get("address_verified"):
            issues.append("Address not verified")
            score -= 5

        if not kyc.get("income_verified"):
            issues.append("Income not verified")
            score -= 5

        if not kyc.get("aml_check_done"):
            issues.append("AML check not completed")
            score -= 5

        # Clamp score to 0-100
        score = max(0.0, score)
        confidence = score / 100

        # If score is too low, flag for human review
        if score < 50:
            return self.low_confidence_response(
                input_reference=f"client:{client_id}",
                reason=f"Data quality too low ({score}%). Issues: {'; '.join(issues)}"
            )

        return self.build_response(
            output={
                "client_id": client_id,
                "data_quality_score": score,
                "issues": issues,
                "can_proceed_to_loan": score >= 70,
                "recommendation": (
                    "PROCEED" if score >= 70
                    else "REVIEW_REQUIRED" if score >= 50
                    else "REJECT"
                )
            },
            confidence=confidence,
            rationale=(
                f"Client profile scored {score}/100. "
                f"{'No major issues found.' if not issues else 'Issues: ' + '; '.join(issues)}"
            ),
            input_reference=f"client:{client_id}"
        )