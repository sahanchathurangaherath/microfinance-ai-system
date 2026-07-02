import os
import django
import random
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User
from apps.loans.models import Loan, LoanApplication
from apps.fraud.models import FraudAlert
from apps.collections.models import DelinquencyCase, CollectionAction
from apps.repayments.models import RepaymentInstallment

def generate_fraud_alerts():
    print("Generating Fraud Alerts...")
    apps = list(LoanApplication.objects.all())
    if not apps:
        print("No LoanApplications found. Cannot generate Fraud Alerts.")
        return
    
    compliance_officers = User.objects.filter(role='compliance_officer')
    officer = compliance_officers.first() if compliance_officers.exists() else None

    # Use names that feel aligned with the seed data context
    alert_types = ['DUPLICATE_IDENTITY', 'APPLICATION_PATTERN', 'PAYMENT_ANOMALY', 'UNUSUAL_AMOUNT', 'KYC_ANOMALY', 'BEHAVIORAL']
    severities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    
    existing_alerts_count = FraudAlert.objects.count()
    if existing_alerts_count > 0:
        print(f"FraudAlerts already exist ({existing_alerts_count}). Skipping generation.")
        return

    # Let's generate 15 fraud alerts
    for _ in range(15):
        app = random.choice(apps)
        alert = FraudAlert.objects.create(
            client=app.client,
            application=app,
            alert_type=random.choice(alert_types),
            severity=random.choice(severities),
            status=random.choice(['OPEN', 'UNDER_INVESTIGATION', 'CLEARED', 'CONFIRMED']),
            fraud_risk_score=random.uniform(50, 95),
            ai_rationale="AI detected suspicious patterns matching historical fraud vectors. High velocity of applications linked to this device footprint.",
            ai_confidence=random.uniform(0.6, 0.95),
            assigned_to=officer if random.choice([True, False]) else None
        )
    print("Created 15 Fraud Alerts.")

def generate_collections_cases():
    print("Generating Collections Cases...")
    
    collections_officers = User.objects.filter(role='collections_officer')
    officer = collections_officers.first() if collections_officers.exists() else None

    existing_case_loans = DelinquencyCase.objects.values_list('loan_id', flat=True)
    
    # Find loans that have OVERDUE installments
    loans_with_overdue = Loan.objects.filter(repayment_schedule__installments__status='OVERDUE').distinct()
    loans_to_process = [l for l in loans_with_overdue if l.id not in existing_case_loans]
    
    if not loans_to_process:
        print("No eligible loans with OVERDUE installments found (or they already have cases).")
        return
        
    created_count = 0
    
    for loan in loans_to_process:
        overdue_insts = RepaymentInstallment.objects.filter(schedule__loan=loan, status='OVERDUE')
        total_overdue = sum(i.amount_due - i.amount_paid for i in overdue_insts)
        
        # Calculate max days overdue
        max_days = max((date.today() - i.due_date).days for i in overdue_insts) if overdue_insts else 0
        if max_days < 0: max_days = 0
        
        # Determine bucket based on days_overdue
        if max_days <= 7:
            bucket = 'BUCKET_1_7'
        elif max_days <= 30:
            bucket = 'BUCKET_8_30'
        else:
            bucket = 'BUCKET_OVER_30'
            
        case = DelinquencyCase.objects.create(
            loan=loan,
            status=random.choice(['OPEN', 'IN_PROGRESS', 'PROMISE_TO_PAY', 'ESCALATED']),
            bucket=bucket,
            total_overdue_amount=total_overdue,
            days_overdue=max_days,
            overdue_installments_count=overdue_insts.count(),
            assigned_to=officer if random.choice([True, False]) else None
        )
        
        # Add a couple of realistic contact actions
        action_types = ['PHONE_CALL', 'SMS', 'EMAIL', 'FIELD_VISIT']
        outcomes = ['NO_ANSWER', 'CONTACTED', 'PROMISED_PAYMENT', 'UNREACHABLE']
        
        for _ in range(random.randint(0, 3)):
            CollectionAction.objects.create(
                case=case,
                action_type=random.choice(action_types),
                outcome=random.choice(outcomes),
                notes="Attempted contact as per collection protocol.",
                performed_by=officer
            )
            
        created_count += 1
            
    print(f"Created {created_count} Delinquency Cases matching seed_data patterns.")

if __name__ == "__main__":
    generate_fraud_alerts()
    generate_collections_cases()
    print("Done generating test data.")
