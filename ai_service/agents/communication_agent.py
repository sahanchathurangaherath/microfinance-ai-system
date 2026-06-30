# ai_service/agents/communication_agent.py
"""
A6 — Communication Agent
LLM upgrade: the local model generates personalized, context-aware messages.
Replaces fixed template substitution with intelligent drafting.
Multilingual: English, Sinhala (si), Tamil (ta) based on client preference.
HARD RULE: A6 only drafts. All messages require officer approval before sending.
Nothing is sent automatically.
"""

from .base_agent import BaseAgent
from typing import Dict
from decouple import config


USE_LLM = config("A6_USE_LLM", default=False, cast=bool)

# Language display names for prompts
_LANGUAGE_NAMES = {
    "en": "English",
    "si": "Sinhala",
    "ta": "Tamil",
}


class CommunicationAgent(BaseAgent):

    def __init__(self):
        super().__init__(agent_id="A6", agent_name="Communication Agent")

    def run(self, input_data: Dict) -> Dict:
        if USE_LLM:
            return self._llm_draft(input_data)
        else:
            return self._template_draft(input_data)

   
    # LLM PATH
   

    def _llm_draft(self, input_data: Dict) -> Dict:
        """
        LLM-powered message drafting.
        The local model generates personalized, tone-adjusted messages.
        Supports Sinhala, Tamil, English based on client preference.
        Falls back to template draft if the LLM fails.
        """
        import json
        from services.llm_client import call_llm
        from services.guardrails import validate_a6_output

        comm_type = input_data.get("comm_type")
        context   = input_data.get("context", {})
        channels  = input_data.get("channels", ["SMS", "EMAIL"])
        language  = context.get("preferred_language", "en")
        lang_name = _LANGUAGE_NAMES.get(language, "English")

        # Build tone instruction based on client relationship context
        missed_payments = int(context.get("missed_payments_count", 0))
        if missed_payments == 0:
            tone = "warm, professional, and friendly"
        elif missed_payments <= 2:
            tone = "professional, empathetic, and gently firm"
        else:
            tone = "professional, firm, and clear — but never threatening"

        channels_str = " AND ".join(channels)

        SYSTEM_PROMPT = f"""You are a professional communication writer for a microfinance institution in Sri Lanka.
You draft client and staff messages for officer review.
Tone: {tone}.
Language: Write in {lang_name}. If Sinhala or Tamil, use appropriate formal script.
Rules:
- Never threaten legal action, court, arrest, or police.
- Never use the word 'blacklist' or 'ban'.
- Always be respectful and dignified.
- SMS must be under 160 characters.
- All messages are for officer review — they will be sent only after approval.
Always respond with valid JSON only."""

        USER_PROMPT = f"""Draft a '{comm_type}' message for the following context:

{json.dumps(context, indent=2, default=str)}

Draft for channels: {channels_str}

Return ONLY this JSON:
{{
  "drafts": [
    {{
      "channel": "SMS",
      "body": "<SMS message, max 160 characters, in {lang_name}>",
      "character_count": <int>
    }},
    {{
      "channel": "EMAIL",
      "subject": "<email subject line, in {lang_name}>",
      "body": "<full email body, in {lang_name}, professional format>"
    }}
  ],
  "tone_applied": "<brief description of tone used>",
  "language_used": "{language}",
  "confidence": <float 0.75-0.95, higher if more personalized>
}}

Only include draft objects for channels in: {json.dumps(channels)}"""

        try:
            output, usage = call_llm(SYSTEM_PROMPT, USER_PROMPT, agent_id=self.agent_id)
        except Exception as e:
            # Fallback to template draft
            return self._template_draft(input_data)

        is_valid, reason = validate_a6_output(output)
        if not is_valid:
            # Guardrail rejected — fallback to template
            return self._template_draft(input_data)

        # Filter drafts to only requested channels
        drafts = [
            d for d in output.get("drafts", [])
            if d.get("channel") in channels
        ]

        return self.build_response(
            output={
                "comm_type":     comm_type,
                "drafts":        drafts,
                "context_used":  context,
                "language_used": output.get("language_used", language),
                "tone_applied":  output.get("tone_applied", ""),
            },
            confidence=float(output.get("confidence", 0.85)),
            rationale=(
                f"A6 drafted {len(drafts)} personalized message(s) for '{comm_type}' "
                f"in {lang_name} ({tone} tone). "
                f"Officer review and approval required before sending."
            ),
            input_reference=f"comm:{comm_type}",
            usage_metadata=usage
        )

   
    # TEMPLATE PATH (original MVP — preserved as fallback)
   

    def _template_draft(self, input_data: Dict) -> Dict:
        """
        Original MVP fixed-template drafting.
        Active when A6_USE_LLM=false, or as fallback when the local LLM fails.
        """
        comm_type = input_data.get("comm_type")
        context   = dict(input_data.get("context", {}))
        channels  = input_data.get("channels", ["SMS", "EMAIL"])

        # Normalize amount/amount_due to prevent template variable mismatch
        if "amount_due" in context and "amount" not in context:
            context["amount"] = context["amount_due"]
        elif "amount" in context and "amount_due" not in context:
            context["amount_due"] = context["amount"]

        SMS_TEMPLATES = {
            "REPAYMENT_REMINDER": (
                "Dear {client_name}, your loan installment of LKR {amount} is due on {due_date}. "
                "Loan: {loan_number}. Please pay on time. Contact: {contact_number}."
            ),
            "OVERDUE_REMINDER": (
                "Dear {client_name}, your loan payment of LKR {amount} for loan {loan_number} "
                "is {days_overdue} day(s) overdue. Contact us: {contact_number}."
            ),
            "PTP_REMINDER": (
                "Dear {client_name}, reminder: LKR {amount} Promise to Pay due tomorrow "
                "({promised_date}). Loan: {loan_number}. Contact: {contact_number}."
            ),
            "LOAN_APPROVED": (
                "Congratulations {client_name}! Loan {loan_number} of LKR {amount} approved. "
                "Monthly: LKR {installment}. First due: {first_due_date}."
            ),
            "LOAN_REJECTED": (
                "Dear {client_name}, application {application_number} was not approved. "
                "Contact us: {contact_number}."
            ),
            "STAFF_ESCALATION_ALERT": (
                "ALERT: Case for loan {loan_number} ({client_name}) escalated to you. "
                "Days overdue: {days_overdue}. Please review."
            ),
            "FRAUD_ALERT_NOTIFY": (
                "FRAUD ALERT: Suspicious activity for client {client_name} (ID: {client_id}). "
                "Score: {fraud_score}. Review alert #{alert_id}."
            ),
        }

        EMAIL_SUBJECTS = {
            "REPAYMENT_REMINDER": "Payment Reminder — Loan {loan_number} Due {due_date}",
            "OVERDUE_REMINDER": "OVERDUE: Loan {loan_number} — {days_overdue} Days Past Due",
            "PTP_REMINDER": "Promise to Pay Reminder — {promised_date}",
            "LOAN_APPROVED": "Your Loan Has Been Approved — {loan_number}",
            "LOAN_REJECTED": "Loan Application {application_number} — Update",
            "STAFF_ESCALATION_ALERT": "Escalation Alert: Loan {loan_number}",
            "FRAUD_ALERT_NOTIFY": "Fraud Alert #{alert_id} — Immediate Review Required",
        }

        sms_template = SMS_TEMPLATES.get(comm_type, "Dear {client_name}, please contact us.")
        subj_template = EMAIL_SUBJECTS.get(comm_type, "Notification")

        try:
            sms_body = sms_template.format(**context)
        except KeyError as e:
            return self.low_confidence_response(
                input_reference=f"comm:{comm_type}",
                reason=f"Missing template variable: {e}"
            )

        try:
            email_subject = subj_template.format(**context)
        except KeyError:
            email_subject = "Notification"

        email_body = (
            f"Dear {context.get('client_name', 'Client')},\n\n"
            f"{sms_body}\n\nMicrofinance Team"
        )

        drafts = []
        if "SMS" in channels:
            drafts.append({
                "channel": "SMS",
                "body": sms_body,
                "character_count": len(sms_body),
            })
        if "EMAIL" in channels:
            drafts.append({
                "channel": "EMAIL",
                "subject": email_subject,
                "body": email_body,
            })

        return self.build_response(
            output={"comm_type": comm_type, "drafts": drafts, "context_used": context},
            confidence=0.92,
            rationale=f"Template draft for '{comm_type}'. Officer approval required.",
            input_reference=f"comm:{comm_type}"
        )