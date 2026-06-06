
"""
A5 — Fraud Detection Agent (Hybrid)
ALWAYS runs rule-based 9-signal check first (fast, deterministic, auditable).
OPTIONALLY runs LLM second-pass debate when A5_USE_LLM=true.
LLM reasons like a prosecutor (find fraud) AND a defense (find innocence),
then synthesises a refined verdict.

HARD RULE: A5 CANNOT freeze, block, or take any enforcement action.
All account actions require Compliance Officer authorization.
"""

from .base_agent import BaseAgent
from typing import Dict, List
from decouple import config


USE_LLM = config("A5_USE_LLM", default=False, cast=bool)


class FraudDetectionAgent(BaseAgent):

    def __init__(self):
        super().__init__(agent_id="A5", agent_name="Fraud Detection Agent")

    def run(self, input_data: Dict) -> Dict:
        """
        Step 1 (always): Rule-based 9-signal check — fast, < 2 seconds.
        Step 2 (optional): LLM debate second-pass — refines verdict.
        """
        client_id = input_data.get("client_id")
        loan_id   = input_data.get("loan_id")

        #  1: RULE-BASED FIRST PASS (always runs) 
        signals, score = self._rule_signals(input_data)
        score     = min(100.0, score)
        severity  = self._severity(score)
        confidence = 0.95 if signals else 0.90

        rule_output = {
            "client_id":         client_id,
            "loan_id":           loan_id,
            "fraud_risk_score":  round(score, 2),
            "severity":          severity,
            "is_suspicious":     score >= 25,
            "signals":           signals,
            "recommended_action": (
                "OPEN_INVESTIGATION" if score >= 50
                else "MONITOR" if score >= 25
                else "CLEAR"
            ),
            # LLM enrichment fields —  2
            "prosecutor_findings":      [],
            "defense_findings":         [],
            "verdict_rationale":        "",
            "llm_refined_score":        None,
            "llm_confidence":           None,
            "investigation_focus":      "",
        }

        rationale = (
            f"Rule-based scan: {len(signals)} signal(s). "
            f"Fraud Risk Score: {round(score, 1)}/100 — {severity}. "
            f"{'Investigation recommended.' if score >= 25 else 'No major indicators.'}"
        )

        # STEP 2: LLM DEBATE SECOND-PASS
        if USE_LLM and signals:
            rule_output, rationale = self._llm_debate(
                rule_output, input_data, signals, rationale
            )

        return self.build_response(
            output=rule_output,
            confidence=rule_output.get("llm_confidence") or confidence,
            rationale=rationale,
            input_reference=f"client:{client_id}|loan:{loan_id}"
        )

   
    # LLM DEBATE SECOND-PASS
  

    def _llm_debate(
        self, rule_output: Dict, input_data: Dict,
        signals: List[Dict], existing_rationale: str
    ) -> tuple[Dict, str]:
        """
        LLM internal debate:
        - 'Prosecutor' sub-prompt: find evidence supporting fraud
        - 'Defense' sub-prompt: find innocent explanations
        - Synthesis: produce refined verdict and investigation focus
        Falls back silently if Gemini fails — rule-based output preserved.
        """
        import json
        from services.gemini_client import call_gemini
        from services.guardrails import validate_a5_output

        client_id = input_data.get("client_id")
        loan_id   = input_data.get("loan_id")

        SYSTEM_PROMPT = """You are a Fraud Analysis Assistant for a microfinance compliance team.
You help Compliance Officers by analysing detected fraud signals.
You flag patterns for INVESTIGATION ONLY — you CANNOT freeze accounts, block clients,
suspend loans, or take any enforcement action. Those require human authorization.
Always respond with valid JSON only. No extra text, no markdown."""

        USER_PROMPT = f"""A rule-based fraud scan found {len(signals)} signal(s) for this case.
Analyse the evidence from two perspectives, then synthesise a verdict.

RULE-BASED SIGNALS DETECTED:
{json.dumps(signals, indent=2)}

CLIENT/APPLICATION CONTEXT:
- Client ID: {client_id}
- Loan ID: {loan_id}
- Identity Data: {json.dumps(input_data.get('identity_data', {}), indent=2)}
- Application Data: {json.dumps(input_data.get('application_data', {}), indent=2)}
- Payment Data: {json.dumps(input_data.get('payment_data', {}), indent=2)}
- KYC Data: {json.dumps(input_data.get('kyc_data', {}), indent=2)}

CURRENT RULE-BASED SCORE: {rule_output['fraud_risk_score']}/100 ({rule_output['severity']})

Analyse as BOTH:
1. PROSECUTOR: What evidence most strongly suggests fraud?
2. DEFENSE: What innocent explanations exist for these signals?
Then synthesise a refined verdict.

IMPORTANT: Do NOT include any account freeze, block, suspend, or enforcement language.
Your output recommends investigation focus only.

Return ONLY this JSON:
{{
  "fraud_risk_score": <float 0-100, your refined score — can only equal or be higher than {rule_output['fraud_risk_score']}>,
  "severity": "<LOW|MEDIUM|HIGH|CRITICAL>",
  "prosecutor_findings": ["key fraud evidence point 1", "point 2"],
  "defense_findings": ["innocent explanation 1", "explanation 2"],
  "verdict_rationale": "<2-3 sentence synthesis for Compliance Officer — NO enforcement language>",
  "confidence": <float 0.0-1.0>,
  "investigation_focus": "<specific area the Compliance Officer should examine first>"
}}"""

        try:
            output = call_gemini(SYSTEM_PROMPT, USER_PROMPT)
        except Exception:
            # Silent fallback — rule-based output preserved unchanged
            return rule_output, existing_rationale

        from services.guardrails import validate_a5_output
        is_valid, reason = validate_a5_output(output)
        if not is_valid:
            # Guardrail rejected — rule-based output preserved
            return rule_output, existing_rationale

        # Hard rule: LLM refined score can only equal or raise severity
        llm_score = float(output["fraud_risk_score"])
        final_score = max(rule_output["fraud_risk_score"], llm_score)

        rule_output["fraud_risk_score"]     = round(final_score, 2)
        rule_output["severity"]             = self._severity(final_score)
        rule_output["is_suspicious"]        = final_score >= 25
        rule_output["prosecutor_findings"]  = output.get("prosecutor_findings", [])
        rule_output["defense_findings"]     = output.get("defense_findings", [])
        rule_output["verdict_rationale"]    = output.get("verdict_rationale", "")
        rule_output["llm_refined_score"]    = round(llm_score, 2)
        rule_output["llm_confidence"]       = float(output["confidence"])
        rule_output["investigation_focus"]  = output.get("investigation_focus", "")
        rule_output["recommended_action"]   = (
            "OPEN_INVESTIGATION" if final_score >= 50
            else "MONITOR" if final_score >= 25
            else "CLEAR"
        )

        rationale = (
            f"Hybrid A5 analysis: Rule score {rule_output['fraud_risk_score']}/100 — "
            f"{rule_output['severity']}. "
            f"{output.get('verdict_rationale', '')} "
            f"Investigation focus: {output.get('investigation_focus', 'General review')}."
        )

        return rule_output, rationale

    
    # RULE-BASED FIRST PASS (original 9 signals — always runs)

    def _rule_signals(self, input_data: Dict) -> tuple[List[Dict], float]:
        signals = []
        score   = 0.0

        identity = input_data.get("identity_data", {})
        app_data = input_data.get("application_data", {})
        payment  = input_data.get("payment_data", {})
        kyc      = input_data.get("kyc_data", {})

        if identity.get("nic_duplicate_count", 0) > 0:
            signals.append({"type": "DUPLICATE_NIC",
                "detail": f"NIC in {identity['nic_duplicate_count']} other records.",
                "weight": 40})
            score += 40

        if identity.get("phone_shared_count", 0) >= 3:
            signals.append({"type": "SHARED_PHONE",
                "detail": f"Phone shared with {identity['phone_shared_count']} clients.",
                "weight": 15})
            score += 15

        if identity.get("address_shared_count", 0) >= 3:
            signals.append({"type": "SHARED_ADDRESS",
                "detail": f"Address shared with {identity['address_shared_count']} clients.",
                "weight": 10})
            score += 10

        if app_data.get("applications_last_30_days", 0) >= 3:
            signals.append({"type": "RAPID_APPLICATIONS",
                "detail": f"{app_data['applications_last_30_days']} applications in 30 days.",
                "weight": 20})
            score += 20

        requested = float(app_data.get("requested_amount", 0))
        income    = float(app_data.get("monthly_income", 0))
        annual    = income * 12
        if annual > 0 and requested > annual * 5:
            signals.append({"type": "UNUSUAL_AMOUNT",
                "detail": f"LKR {requested:,.0f} exceeds 5x annual income ({annual:,.0f}).",
                "weight": 20})
            score += 20

        if requested > 0 and requested % 100000 == 0:
            signals.append({"type": "ROUND_AMOUNT_PATTERN",
                "detail": f"Exact round number: LKR {requested:,.0f}.",
                "weight": 5})
            score += 5

        if payment.get("reversals_last_7_days", 0) >= 2:
            signals.append({"type": "PAYMENT_REVERSALS",
                "detail": f"{payment['reversals_last_7_days']} reversals in 7 days.",
                "weight": 25})
            score += 25

        mins = kyc.get("completion_time_minutes", 999)
        if 0 < mins < 10:
            signals.append({"type": "KYC_RUSH",
                "detail": f"KYC completed in {mins} minutes.",
                "weight": 10})
            score += 10

        return signals, score

    def _severity(self, score: float) -> str:
        if score >= 70:   return "CRITICAL"
        elif score >= 50: return "HIGH"
        elif score >= 25: return "MEDIUM"
        else:             return "LOW"