from django.test import TestCase
from unittest.mock import patch
from rest_framework.test import APIClient
from rest_framework import status

from apps.users.models import User
from apps.clients.models import Client, ClientIncome
from apps.loans.models import (
    LoanProduct, LoanApplication, CashflowAssessment,
    DisbursementCondition, Loan, Disbursement
)
from apps.approvals.models import ApprovalWorkflow, ApprovalDecision


class LoanWorkflowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.loan_officer = User.objects.create_user(
            username='loan_officer',
            password='password',
            role='loan_officer'
        )
        self.risk_analyst = User.objects.create_user(
            username='risk_analyst',
            password='password',
            role='risk_analyst'
        )

        self.client_profile = Client.objects.create(
            nic_number='123456789V',
            first_name='Test',
            last_name='User',
            date_of_birth='1990-01-01',
            gender='M',
            phone_primary='0771234567',
            status='PENDING',
            registered_by=self.loan_officer,
        )
        ClientIncome.objects.create(
            client=self.client_profile,
            income_source='SALARY',
            monthly_income=50000,
            other_income=0,
            monthly_expenses=10000,
            existing_debt_monthly=5000,
            number_of_dependents=2,
        )

        self.loan_product = LoanProduct.objects.create(
            name='Working Capital',
            description='Test loan product',
            min_amount=10000,
            max_amount=500000,
            min_duration_months=6,
            max_duration_months=24,
            interest_rate=18.0,
        )

        self.application = LoanApplication.objects.create(
            client=self.client_profile,
            loan_product=self.loan_product,
            requested_amount=100000,
            requested_duration_months=12,
            loan_purpose='WORKING_CAPITAL',
            purpose_description='Test loan',
            created_by=self.loan_officer,
            status='DRAFT',
        )
        CashflowAssessment.objects.create(
            application=self.application,
            monthly_income=50000,
            other_income=0,
            monthly_expenses=10000,
            existing_loan_payments=5000,
            proposed_monthly_payment=8000,
            net_cashflow=27000,
            debt_to_income_ratio=0.3,
        )

    def test_submit_application_advances_to_ai_screening(self):
        self.client.force_authenticate(user=self.loan_officer)

        response = self.client.post(f'/api/loans/applications/{self.application.id}/submit/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'AI_SCREENING')

        history = self.application.status_history.order_by('timestamp')
        self.assertEqual(history.count(), 2)
        self.assertEqual(history[0].to_status, 'SUBMITTED')
        self.assertEqual(history[1].to_status, 'AI_SCREENING')

    @patch('apps.audit.policy_engine.evaluate_and_run_agent')
    def test_trigger_risk_assessment_from_submitted_moves_to_risk_assessed(self, mock_evaluate):
        self.application.status = 'SUBMITTED'
        self.application.save()

        mock_evaluate.return_value = {
            'output': {
                'risk_score': 50,
                'risk_category': 'MEDIUM',
                'factor_scores': {},
                'default_signals': [],
            },
            'confidence': 0.8,
            'rationale': 'Test rationale',
        }

        self.client.force_authenticate(user=self.risk_analyst)
        response = self.client.post(f'/api/loans/applications/{self.application.id}/risk-assess/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'RISK_ASSESSED')

    def test_process_disbursement_after_approved_application(self):
        finance_staff = User.objects.create_user(
            username='finance_staff',
            password='password',
            role='finance_staff'
        )
        branch_manager = User.objects.create_user(
            username='branch_manager',
            password='password',
            role='branch_manager'
        )

        self.application.status = 'APPROVED'
        self.application.save()

        workflow = ApprovalWorkflow.objects.create(
            application=self.application,
            requires_committee=False
        )
        ApprovalDecision.objects.create(
            workflow=workflow,
            step='BRANCH_MANAGER',
            decision='APPROVED',
            decided_by=branch_manager,
            comments='Approved for disbursement'
        )

        DisbursementCondition.objects.create(
            application=self.application,
            condition_text='Collateral verified',
            is_met=True
        )
        DisbursementCondition.objects.create(
            application=self.application,
            condition_text='Insurance confirmed',
            is_met=True
        )

        self.client.force_authenticate(user=finance_staff)
        response = self.client.post(f'/api/loans/disbursements/{self.application.id}/process/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'DISBURSED')
        self.assertTrue(Loan.objects.filter(application=self.application).exists())
        self.assertTrue(Disbursement.objects.filter(application=self.application).exists())
        self.assertEqual(response.data['message'], 'Loan disbursed successfully.')
