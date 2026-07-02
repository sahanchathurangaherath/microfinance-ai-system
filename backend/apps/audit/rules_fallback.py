# backend/apps/audit/rules_fallback.py
"""
Local fallback rules engine for AI agents A1-A6.
Guarantees fail-safe processing when the FastAPI AI Service is down.
Outputs are structured identically to the AI Service agent responses.
"""
from datetime import datetime, date
from typing import Dict, List, Tuple


def run_local_rules(agent_id: str, input_data: Dict) -> Dict:
    """
    Dispatcher to run the rule-based backup for a given agent.
    """
    if agent_id == "A1":
        return a1_validate_client_rules(input_data)
    elif agent_id == "A2":
        return a2_risk_score_rules(input_data)
    elif agent_id == "A3":
        return a3_recommendation_rules(input_data)
    elif agent_id == "A4":
        return a4_monitoring_rules(input_data)
    elif agent_id == "A5":
        return a5_fraud_rules(input_data)
    elif agent_id == "A6":
        return a6_communication_rules(input_data)
    else:
        raise ValueError(f"Unknown agent: {agent_id}")


# A1 Data Collection Fallback
def a1_validate_client_rules(input_data: Dict) -> Dict:
    client_id = input_data.get("client_id")
    client = input_data.get("client_data", {})
    kyc = input_data.get("kyc_data", {})

    score = 0.0
    missing = []
    signals = []

    # Identity checks
    if client.get("nic_number"): score += 15
    else: missing.append("nic_number")
    if client.get("first_name"): score += 5
    else: missing.append("first_name")
    if client.get("last_name"): score += 5
    else: missing.append("last_name")
    if client.get("date_of_birth"): score += 5
    else: missing.append("date_of_birth")

    # Contact checks
    if client.get("phone_primary"): score += 5
    else: missing.append("phone_primary")

    # KYC Checklist checks
    if kyc.get("address_verified"): score += 10
    else: missing.append("address_verified")
    if kyc.get("income_verified"): score += 15
    else: missing.append("income_verified")
    if kyc.get("id_document_uploaded"): score += 15
    else: missing.append("id_document_uploaded")
    if kyc.get("income_document_uploaded"): score += 15
    else: missing.append("income_document_uploaded")

    # Business/Income checks
    if client.get("income", {}).get("monthly_income") or client.get("monthly_income"):
        score += 10
    else:
        missing.append("monthly_income")
        signals.append("Income data missing")

    score = min(100.0, score)
    confidence = 0.85 if not missing else max(0.4, 0.85 - len(missing) * 0.05)

    rationale = (
        f"Local rule fallback scan. Data quality score: {round(score, 1)}/100. "
        f"Missing fields: {', '.join(missing) if missing else 'None'}. "
        f"Signals: {', '.join(signals) if signals else 'None'}."
    )

    status = "SUCCESS"
    if confidence < 0.5:
        status = "REQUIRES_HUMAN_REVIEW"

    return {
        "agent_id": "A1",
        "agent_name": "Data Collection Agent",
        "timestamp": datetime.utcnow().isoformat(),
        "status": status,
        "confidence": round(confidence, 2),
        "rationale": rationale,
        "input_reference": f"client:{client_id}",
        "output": {
            "client_id": client_id,
            "data_quality_score": round(score, 2),
            "missing_critical_fields": missing,
            "consistency_flags": [],
            "fraud_signals": signals,
        }
    }


# A2 Risk Assessment Fallback
def a2_risk_score_rules(input_data: Dict) -> Dict:
    loan_id = input_data.get("loan_id")
    client = input_data.get("client_data", {})
    loan = input_data.get("loan_data", {})
    history = input_data.get("repayment_history", {}) or {}

    scores = {}
    signals = []

    # Factor 1: DTI (25 pts)
    dti = float(loan.get("debt_to_income_ratio") or 0)
    if dti <= 0.30: scores["dti"] = 25.0
    elif dti <= 0.50: scores["dti"] = 15.0
    else:
        scores["dti"] = 0.0
        signals.append(f"High DTI ratio: {round(dti * 100, 1)}%")

    # Factor 2: LTI (20 pts)
    monthly_income = float(client.get("monthly_income") or 0)
    loan_amount = float(loan.get("requested_amount") or 0)
    annual_income = monthly_income * 12
    lti = 0.0
    if annual_income > 0:
        lti = loan_amount / annual_income
        if lti <= 2.0: scores["lti"] = 20.0
        elif lti <= 4.0: scores["lti"] = 10.0
        else:
            scores["lti"] = 0.0
            signals.append(f"Loan is {round(lti, 1)}x annual income")
    else:
        scores["lti"] = 0.0
        signals.append("No income data — cannot calculate LTI")

    # Factor 3: KYC completeness (15 pts)
    kyc_quality = float(client.get("data_quality_score") or 0)
    scores["kyc"] = (kyc_quality / 100) * 15

    # Factor 4: Income stability (15 pts)
    years = int(client.get("years_in_operation") or 0)
    if years >= 3: scores["income_stability"] = 15.0
    elif years >= 1: scores["income_stability"] = 8.0
    else:
        scores["income_stability"] = 3.0
        signals.append("Business less than 1 year — income stability risk")

    # Factor 5: Repayment history (15 pts)
    missed = int(history.get("missed_payments") or 0)
    prev_cnt = int(history.get("previous_loans_count") or 0)
    if prev_cnt == 0: scores["repayment"] = 10.0
    elif missed == 0: scores["repayment"] = 15.0
    elif missed <= 2: scores["repayment"] = 8.0
    else:
        scores["repayment"] = 0.0
        signals.append(f"Client has {missed} missed payments")

    # Factor 6: Dependents (10 pts)
    dependents = int(client.get("number_of_dependents") or 0)
    if dependents <= 2: scores["dependents"] = 10.0
    elif dependents <= 4: scores["dependents"] = 7.0
    else:
        scores["dependents"] = 4.0
        signals.append(f"High dependents count: {dependents}")

    risk_score = sum(scores.values())
    if risk_score >= 70:
        risk_category = "LOW"
        required_action = "LOAN_OFFICER_REVIEW"
    elif risk_score >= 40:
        risk_category = "MEDIUM"
        required_action = "RISK_ANALYST_REQUIRED"
    else:
        risk_category = "HIGH"
        required_action = "BRANCH_MANAGER_ESCALATION"

    rationale = (
        f"Local rule fallback scan: Risk Score: {round(risk_score, 1)}/100 ({risk_category}). "
        f"Factors: DTI={scores.get('dti')}, LTI={scores.get('lti')}, KYC={scores.get('kyc')}, "
        f"Stability={scores.get('income_stability')}, Repayment={scores.get('repayment')}, Dependents={scores.get('dependents')}. "
        f"Warnings: {', '.join(signals) if signals else 'None'}."
    )

    return {
        "agent_id": "A2",
        "agent_name": "Risk Assessment Agent",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "SUCCESS",
        "confidence": 0.90,
        "rationale": rationale,
        "input_reference": f"loan:{loan_id}",
        "output": {
            "loan_id": loan_id,
            "risk_score": round(risk_score, 2),
            "risk_category": risk_category,
            "factor_scores": {
                "dti_score": scores.get("dti", 0.0),
                "lti_score": scores.get("lti", 0.0),
                "kyc_score": scores.get("kyc", 0.0),
                "income_stability_score": scores.get("income_stability", 0.0),
                "repayment_history_score": scores.get("repayment", 0.0),
                "dependents_score": scores.get("dependents", 0.0),
            },
            "default_signals": signals,
            "required_action": required_action,
        }
    }


# A3 Recommendation Fallback
def a3_recommendation_rules(input_data: Dict) -> Dict:
    loan_id = input_data.get("loan_id")
    risk_score = float(input_data.get("risk_score") or 0)
    risk_category = input_data.get("risk_category", "HIGH")
    signals = input_data.get("default_signals") or []
    kyc_score = float(input_data.get("kyc_score") or 0)
    requested_amount = float(input_data.get("requested_amount") or 0)
    monthly_income = float(input_data.get("monthly_income") or 0)
    duration_months = int(input_data.get("requested_duration_months") or 12)
    dti = float(input_data.get("debt_to_income_ratio") or 0)

    reasons = []
    recommendation = None
    recommended_amount = None

    if kyc_score < 60:
        recommendation = "RECOMMEND_MORE_DOCUMENTS"
        reasons.append(f"KYC score only {round(kyc_score, 1)}% — documents incomplete.")
    elif risk_category == "HIGH" and risk_score < 30:
        recommendation = "RECOMMEND_REJECTION"
        reasons.append(f"Risk score {round(risk_score, 1)}/100 is critically low.")
        for s in signals[:2]:
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
    else:
        recommendation = "RECOMMEND_ESCALATION"
        reasons.append("Insufficient confidence for a clear recommendation.")

    confidence_map = {
        "RECOMMEND_APPROVAL": 0.85,
        "RECOMMEND_REJECTION": 0.90,
        "RECOMMEND_REDUCED_AMOUNT": 0.75,
        "RECOMMEND_MORE_DOCUMENTS": 0.95,
        "RECOMMEND_ESCALATION": 0.70,
    }
    confidence = confidence_map.get(recommendation, 0.70)

    explanation = (
        f"A3 local rule fallback recommendation: {recommendation}. "
        f"Risk score {round(risk_score,1)}/100 ({risk_category}). "
        f"Primary Reason: {reasons[0] if reasons else 'Calculated via rule guidelines.'}"
    )

    return {
        "agent_id": "A3",
        "agent_name": "Recommendation Agent",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "SUCCESS",
        "confidence": round(confidence, 2),
        "rationale": explanation,
        "input_reference": f"loan:{loan_id}",
        "output": {
            "loan_id": loan_id,
            "recommendation_type": recommendation,
            "recommended_amount": recommended_amount,
            "recommended_duration_months": duration_months,
            "explanation": explanation,
            "reasons": reasons,
        }
    }


# A4 Monitoring Fallback
def a4_monitoring_rules(input_data: Dict) -> Dict:
    loans = input_data.get("loans", [])
    today_str = input_data.get("today") or str(date.today())
    today = date.fromisoformat(today_str)

    overdue_cases = []
    early_overdue_count = 0
    warning_count = 0
    critical_count = 0

    for loan in loans:
        loan_id = loan.get("loan_id")
        loan_number = loan.get("loan_number")
        installments = loan.get("installments", [])

        for inst in installments:
            if inst.get("status") in ["PAID", "WAIVED"]:
                continue

            due_date = date.fromisoformat(inst["due_date"])
            if due_date >= today:
                continue

            days_overdue = (today - due_date).days
            outstanding = float(inst.get("outstanding", inst.get("amount_due", 0)))
            
            # Simple bucket classification
            if days_overdue <= 7:
                bucket = "1-7 Days"
                severity = "EARLY_OVERDUE"
                recommended_action = "SEND_SMS_REMINDER"
                early_overdue_count += 1
            elif days_overdue <= 30:
                bucket = "8-30 Days"
                severity = "WARNING"
                recommended_action = "PLACE_OFFICER_CALL"
                warning_count += 1
            else:
                bucket = ">30 Days"
                severity = "CRITICAL"
                recommended_action = "DISPATCH_FIELD_VISIT"
                critical_count += 1

            overdue_cases.append({
                "loan_id": loan_id,
                "loan_number": loan_number,
                "installment_id": inst.get("installment_id"),
                "installment_number": inst.get("installment_number"),
                "due_date": str(due_date),
                "days_overdue": days_overdue,
                "outstanding_amount": outstanding,
                "bucket": bucket,
                "severity": severity,
                "recommended_action": recommended_action,
                "predicted_default_probability": None,
                "behavioral_pattern_label": None,
                "llm_recommended_action": None,
            })

    total_loans = len(loans)
    overdue_count = len({c["loan_id"] for c in overdue_cases})
    at_risk_rate = round(overdue_count / total_loans * 100, 1) if total_loans > 0 else 0

    rationale = (
        f"Local rule fallback scan: Scanned {total_loans} active loan(s). "
        f"{overdue_count} loan(s) have overdue installments ({at_risk_rate}% portfolio at risk). "
        f"Buckets: {warning_count} warning, {critical_count} critical."
    )

    return {
        "agent_id": "A4",
        "agent_name": "Monitoring Agent",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "SUCCESS",
        "confidence": 0.95,
        "rationale": rationale,
        "input_reference": f"portfolio_scan:{today_str}",
        "output": {
            "scan_date": today_str,
            "total_loans_scanned": total_loans,
            "overdue_cases": overdue_cases,
            "overdue_loan_count": overdue_count,
            "portfolio_at_risk_percent": at_risk_rate,
            "llm_prediction_applied": False,
            "summary": {
                "early_overdue_1_7_days": early_overdue_count,
                "warning_8_30_days": warning_count,
                "critical_over_30_days": critical_count,
            }
        }
    }


# A5 Fraud Detection Fallback
def a5_fraud_rules(input_data: Dict) -> Dict:
    client_id = input_data.get("client_id")
    loan_id = input_data.get("loan_id")
    identity = input_data.get("identity_data", {})
    app_data = input_data.get("application_data", {})
    payment = input_data.get("payment_data", {})
    kyc = input_data.get("kyc_data", {})

    signals = []
    score = 0.0

    if identity.get("nic_duplicate_count", 0) > 0:
        signals.append({"type": "DUPLICATE_NIC", "detail": f"NIC in other records.", "weight": 40})
        score += 40
    if identity.get("phone_shared_count", 0) >= 3:
        signals.append({"type": "SHARED_PHONE", "detail": f"Phone shared.", "weight": 15})
        score += 15
    if identity.get("address_shared_count", 0) >= 3:
        signals.append({"type": "SHARED_ADDRESS", "detail": f"Address shared.", "weight": 10})
        score += 10
    if app_data.get("applications_last_30_days", 0) >= 3:
        signals.append({"type": "RAPID_APPLICATIONS", "detail": f"Rapid applications.", "weight": 20})
        score += 20

    requested = float(app_data.get("requested_amount", 0))
    income = float(app_data.get("monthly_income", 0))
    if income > 0 and requested > income * 12 * 5:
        signals.append({"type": "UNUSUAL_AMOUNT", "detail": f"Exceeds 5x annual income.", "weight": 20})
        score += 20
    if requested > 0 and requested % 100000 == 0:
        signals.append({"type": "ROUND_AMOUNT_PATTERN", "detail": f"Exact round number.", "weight": 5})
        score += 5
    if payment.get("reversals_last_7_days", 0) >= 2:
        signals.append({"type": "PAYMENT_REVERSALS", "detail": f"Payment reversals.", "weight": 25})
        score += 25

    mins = kyc.get("completion_time_minutes", 999)
    if 0 < mins < 10:
        signals.append({"type": "KYC_RUSH", "detail": f"KYC completed rapidly.", "weight": 10})
        score += 10

    score = min(100.0, score)
    if score >= 70: severity = "CRITICAL"
    elif score >= 50: severity = "HIGH"
    elif score >= 25: severity = "MEDIUM"
    else: severity = "LOW"

    confidence = 0.95 if signals else 0.90
    rationale = (
        f"Local rule fallback scan: {len(signals)} signal(s). "
        f"Fraud Risk Score: {round(score, 1)}/100 — {severity}."
    )

    return {
        "agent_id": "A5",
        "agent_name": "Fraud Detection Agent",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "SUCCESS",
        "confidence": confidence,
        "rationale": rationale,
        "input_reference": f"client:{client_id}|loan:{loan_id}",
        "output": {
            "client_id": client_id,
            "loan_id": loan_id,
            "fraud_risk_score": round(score, 2),
            "severity": severity,
            "is_suspicious": score >= 25,
            "signals": signals,
            "recommended_action": (
                "OPEN_INVESTIGATION" if score >= 50
                else "MONITOR" if score >= 25
                else "CLEAR"
            ),
            "prosecutor_findings": [],
            "defense_findings": [],
            "verdict_rationale": "",
            "llm_refined_score": None,
            "llm_confidence": None,
            "investigation_focus": "",
        }
    }


# A6 Communication Fallback
def a6_communication_rules(input_data: Dict) -> Dict:
    comm_type = input_data.get("comm_type")
    context = input_data.get("context", {})
    channels = input_data.get("channels") or ["SMS", "EMAIL"]

    client_name = f"{context.get('client_first_name', '')} {context.get('client_last_name', '')}".strip() or "Valued Client"
    amount = context.get("requested_amount", context.get("loan_amount", "0"))
    due_date = context.get("due_date", "due date")

    drafts = []
    
    # Simple message templates
    if comm_type == "WELCOME":
        subject = "Welcome to MicroFinance"
        body = f"Dear {client_name}, welcome to our MicroFinance program! Your loan application has been registered."
    elif comm_type == "REPAYMENT_REMINDER":
        subject = "Repayment Reminder"
        body = f"Dear {client_name}, this is a reminder that your installment is due on {due_date}. Thank you."
    elif comm_type == "DELINQUENCY_NOTICE":
        subject = "Urgent: Delinquent Payment Notice"
        body = f"Dear {client_name}, your repayment is overdue. Please contact your loan officer immediately."
    else:
        subject = "Notification update"
        body = f"Dear {client_name}, this is an update regarding your application."

    for channel in channels:
        drafts.append({
            "channel": channel,
            "subject": subject if channel == "EMAIL" else "",
            "message_body": body,
            "language": "en",
        })

    return {
        "agent_id": "A6",
        "agent_name": "Communication Agent",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "SUCCESS",
        "confidence": 0.95,
        "rationale": f"Local rule fallback template messaging generated for welcome/repayment/delinquency notice.",
        "input_reference": f"comm:{comm_type}",
        "output": {
            "drafts": drafts
        }
    }
