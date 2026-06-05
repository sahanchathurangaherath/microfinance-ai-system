from .base_agent import BaseAgent
from typing import Dict


class CommunicationAgent(BaseAgent):
    """
    A6: Communication Agent
    Drafts SMS and email messages for officer review.
    NEVER sends messages directly — all sends require officer approval.
    """

    def __init__(self):
        super().__init__(agent_id="A6", agent_name="Communication Agent")

    #  TEMPLATES
    SMS_TEMPLATES = {
        "REPAYMENT_REMINDER": (
            "Dear {client_name}, your loan installment of LKR {amount} is due on {due_date}. "
            "Loan: {loan_number}. Please make your payment on time. "
            "Contact us: {contact_number}."
        ),
        "OVERDUE_REMINDER": (
            "Dear {client_name}, your loan payment of LKR {amount} for loan {loan_number} "
            "is now {days_overdue} day(s) overdue. Please contact us immediately at {contact_number}."
        ),
        "PTP_REMINDER": (
            "Dear {client_name}, this is a reminder of your Promise to Pay of LKR {amount} "
            "due tomorrow ({promised_date}). Loan: {loan_number}. Contact: {contact_number}."
        ),
        "LOAN_APPROVED": (
            "Congratulations {client_name}! Your loan {loan_number} of LKR {amount} "
            "has been approved and disbursed. Monthly installment: LKR {installment}. "
            "First due date: {first_due_date}."
        ),
        "LOAN_REJECTED": (
            "Dear {client_name}, we regret to inform you that your loan application "
            "{application_number} has not been approved at this time. "
            "Contact us for details: {contact_number}."
        ),
        "STAFF_ESCALATION_ALERT": (
            "ALERT: Delinquency case for loan {loan_number} (Client: {client_name}) "
            "has been escalated to you. Days overdue: {days_overdue}. "
            "Please review immediately."
        ),
        "FRAUD_ALERT_NOTIFY": (
            "FRAUD ALERT: Suspicious activity detected for client {client_name} "
            "(ID: {client_id}). Risk Score: {fraud_score}. Please review alert #{alert_id}."
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

    def run(self, input_data: Dict) -> Dict:
        comm_type = input_data.get("comm_type")
        context = input_data.get("context", {})
        channels = input_data.get("channels", ["SMS", "EMAIL"])

        if comm_type not in self.SMS_TEMPLATES:
            return self.low_confidence_response(
                input_reference=f"comm:{comm_type}",
                reason=f"Unknown communication type: {comm_type}"
            )

        sms_template = self.SMS_TEMPLATES.get(comm_type, "")
        subject_template = self.EMAIL_SUBJECTS.get(comm_type, "Notification")

        try:
            sms_body = sms_template.format(**context)
        except KeyError as e:
            return self.low_confidence_response(
                input_reference=f"comm:{comm_type}",
                reason=f"Missing context variable for SMS template: {e}"
            )

        try:
            email_subject = subject_template.format(**context)
            email_body = self._build_email_body(comm_type, context)
        except KeyError as e:
            email_subject = "Notification"
            email_body = sms_body

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
            output={
                "comm_type": comm_type,
                "drafts": drafts,
                "context_used": context,
            },
            confidence=0.92,
            rationale=(
                f"A6 drafted {len(drafts)} message(s) for '{comm_type}'. "
                f"Officer review and approval required before sending."
            ),
            input_reference=f"comm:{comm_type}"
        )

    def _build_email_body(self, comm_type: str, context: dict) -> str:
        client_name = context.get("client_name", "Dear Client")

        bodies = {
            "REPAYMENT_REMINDER": (
                f"Dear {client_name},\n\n"
                f"This is a friendly reminder that your loan installment of "
                f"LKR {context.get('amount', 'N/A')} for loan "
                f"{context.get('loan_number', 'N/A')} is due on "
                f"{context.get('due_date', 'N/A')}.\n\n"
                f"Please ensure sufficient funds are available in your account "
                f"or visit our branch to make your payment.\n\n"
                f"If you have any questions, please contact us at "
                f"{context.get('contact_number', 'N/A')}.\n\n"
                f"Thank you for your continued trust.\n\nMicrofinance Team"
            ),
            "OVERDUE_REMINDER": (
                f"Dear {client_name},\n\n"
                f"Your loan payment of LKR {context.get('amount', 'N/A')} "
                f"for loan {context.get('loan_number', 'N/A')} is now "
                f"{context.get('days_overdue', 'N/A')} day(s) overdue.\n\n"
                f"Late payments may incur additional charges. "
                f"Please contact us immediately at "
                f"{context.get('contact_number', 'N/A')} to discuss your options.\n\n"
                f"Microfinance Team"
            ),
            "LOAN_APPROVED": (
                f"Dear {client_name},\n\n"
                f"We are pleased to inform you that your loan application has been "
                f"approved and disbursed.\n\n"
                f"Loan Number    : {context.get('loan_number', 'N/A')}\n"
                f"Amount         : LKR {context.get('amount', 'N/A')}\n"
                f"Monthly Inst.  : LKR {context.get('installment', 'N/A')}\n"
                f"First Due Date : {context.get('first_due_date', 'N/A')}\n\n"
                f"Please ensure timely repayments to maintain a good credit history.\n\n"
                f"Microfinance Team"
            ),
            "LOAN_REJECTED": (
                f"Dear {client_name},\n\n"
                f"Thank you for applying with us. After careful review of your application "
                f"{context.get('application_number', 'N/A')}, we are unable to approve "
                f"your loan at this time.\n\n"
                f"Please contact us at {context.get('contact_number', 'N/A')} for "
                f"more information or to discuss alternative options.\n\n"
                f"Microfinance Team"
            ),
        }

        return bodies.get(comm_type, f"Dear {client_name},\n\nPlease contact us.\n\nMicrofinance Team")