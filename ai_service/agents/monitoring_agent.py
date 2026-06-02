
"""
A4 — Monitoring Agent
Rule-based overdue detection (always runs) +
Optional LLM behavioural pattern prediction (when A4_USE_LLM=true).
A4 cannot freeze accounts or modify loans — only flags and alerts.
"""

from .base_agent import BaseAgent
from typing import Dict, List
from datetime import date
from decouple import config


USE_LLM = config("A4_USE_LLM", default=False, cast=bool)


class MonitoringAgent(BaseAgent):

    def __init__(self):
        super().__init__(agent_id="A4", agent_name="Monitoring Agent")

    def run(self, input_data: Dict) -> Dict:
        """
        Always runs rule-based overdue scan.
        If A4_USE_LLM=true, also runs LLM behavioural prediction per overdue loan.
        """
        loans     = input_data.get("loans", [])
        today_str = input_data.get("today", str(date.today()))
        today     = date.fromisoformat(today_str)

        overdue_cases  = []
        healthy_count  = 0
        warning_count  = 0
        critical_count = 0

        for loan in loans:
            loan_id     = loan.get("loan_id")
            loan_number = loan.get("loan_number")
            installments = loan.get("installments", [])

            for inst in installments:
                if inst.get("status") in ["PAID", "WAIVED"]:
                    continue

                due_date = date.fromisoformat(inst["due_date"])
                if due_date >= today:
                    continue

                days_overdue = (today - due_date).days
                outstanding  = float(inst.get("outstanding", inst.get("amount_due", 0)))
                bucket       = self._classify_bucket(days_overdue)
                severity     = self._severity(days_overdue)

                if severity == "HEALTHY":   healthy_count  += 1
                elif severity == "WARNING": warning_count  += 1
                else:                       critical_count += 1

                case = {
                    "loan_id":            loan_id,
                    "loan_number":        loan_number,
                    "installment_id":     inst.get("installment_id"),
                    "installment_number": inst.get("installment_number"),
                    "due_date":           str(due_date),
                    "days_overdue":       days_overdue,
                    "outstanding_amount": outstanding,
                    "bucket":             bucket,
                    "severity":           severity,
                    "recommended_action": self._recommend_action(days_overdue),
                    # LLM fields — populated below if USE_LLM=true
                    "predicted_default_probability": None,
                    "behavioral_pattern_label":      None,
                    "llm_recommended_action":        None,
                }
                overdue_cases.append(case)

        # LLM second pass — behavioural prediction per overdue loan
        if USE_LLM and overdue_cases:
            overdue_cases = self._llm_predict_patterns(overdue_cases, loans)

        total_loans      = len(loans)
        overdue_loan_ids = {c["loan_id"] for c in overdue_cases}
        overdue_count    = len(overdue_loan_ids)
        at_risk_rate     = round(overdue_count / total_loans * 100, 1) if total_loans > 0 else 0

        rationale = (
            f"Scanned {total_loans} active loan(s). "
            f"{overdue_count} loan(s) have overdue installments ({at_risk_rate}% portfolio at risk). "
            f"Buckets: {warning_count} warning (8–30 days), {critical_count} critical (>30 days)."
        )

        return self.build_response(
            output={
                "scan_date":                today_str,
                "total_loans_scanned":      total_loans,
                "overdue_cases":            overdue_cases,
                "overdue_loan_count":       overdue_count,
                "portfolio_at_risk_percent": at_risk_rate,
                "llm_prediction_applied":   USE_LLM,
                "summary": {
                    "healthy":             healthy_count,
                    "warning_1_30_days":   warning_count,
                    "critical_over_30_days": critical_count,
                }
            },
            confidence=0.98,
            rationale=rationale,
            input_reference=f"portfolio_scan:{today_str}"
        )

   
    # LLM PREDICTION LAYER

    def _llm_predict_patterns(self, overdue_cases: List[Dict], all_loans: List[Dict]) -> List[Dict]:
        """
        For each overdue loan, call Gemini to classify the payment
        behaviour pattern and predict default probability.
        Falls back silently if Gemini fails — rule-based data remains intact.
        """
        import json
        from services.gemini_client import call_gemini
        from services.guardrails import validate_a4_llm_output

        # Build a lookup of full installment history per loan
        loan_history = {
            loan["loan_id"]: loan.get("installments", [])
            for loan in all_loans
        }

        # Process each unique overdue loan (not each installment)
        processed_loan_ids = set()
        predictions = {}

        for case in overdue_cases:
            loan_id = case["loan_id"]
            if loan_id in processed_loan_ids:
                continue
            processed_loan_ids.add(loan_id)

            history = loan_history.get(loan_id, [])

            SYSTEM_PROMPT = """You are a Portfolio Risk Analyst for a microfinance institution.
Analyse repayment patterns and predict default probability.
You assist the Collections Officer — you cannot freeze accounts or take direct action.
Always respond with valid JSON only."""

            USER_PROMPT = f"""Analyse the repayment behaviour for loan {case['loan_number']}.

INSTALLMENT HISTORY:
{json.dumps(history, indent=2, default=str)}

CURRENT OVERDUE STATUS:
- Days Overdue: {case['days_overdue']}
- Outstanding Amount: LKR {case['outstanding_amount']:,.2f}
- Arrears Bucket: {case['bucket']}

Classify the payment pattern and predict default probability.

Return ONLY this JSON:
{{
  "predicted_default_probability": <float 0.0-1.0>,
  "behavioral_pattern_label": "<one of: CONSISTENT_PAYER | EARLY_DETERIORATION | SEASONAL_STRESS | RECOVERING | CHRONIC_LATE | FIRST_DEFAULT | UNKNOWN>",
  "recommended_action": "<specific action for Collections Officer>",
  "pattern_reasoning": "<1-2 sentence explanation>"
}}"""

            try:
                output = call_gemini(SYSTEM_PROMPT, USER_PROMPT)
                is_valid, _ = validate_a4_llm_output(output)
                if is_valid:
                    predictions[loan_id] = output
            except Exception:
                # Silent fallback — rule-based data remains; LLM fields stay None
                pass

        # Apply predictions to all cases for that loan
        for case in overdue_cases:
            pred = predictions.get(case["loan_id"])
            if pred:
                case["predicted_default_probability"] = float(pred["predicted_default_probability"])
                case["behavioral_pattern_label"]      = pred["behavioral_pattern_label"]
                case["llm_recommended_action"]        = pred["recommended_action"]

        return overdue_cases

   
    # RULE-BASED HELPERS (unchanged from original)
   
    def _classify_bucket(self, days: int) -> str:
        if days <= 7:   return "BUCKET_1_7"
        elif days <= 30: return "BUCKET_8_30"
        else:            return "BUCKET_OVER_30"

    def _severity(self, days: int) -> str:
        if days <= 7:   return "HEALTHY"
        elif days <= 30: return "WARNING"
        else:            return "CRITICAL"

    def _recommend_action(self, days: int) -> str:
        if days <= 7:    return "SEND_REMINDER"
        elif days <= 30: return "COLLECTIONS_CONTACT"
        elif days <= 60: return "ESCALATE_TO_MANAGER"
        else:            return "CONSIDER_LEGAL_OR_WRITEOFF"