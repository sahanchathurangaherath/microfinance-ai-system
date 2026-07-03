from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status

from apps.users.models import User
from apps.clients.models import Client, ClientIncome
from apps.loans.models import LoanProduct, LoanApplication, CashflowAssessment


class ApprovalWorkflowTests(APITestCase):
    def setUp(self):
        self.client = self.client
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
        self.branch_manager = User.objects.create_user(
            username='branch_manager',
            password='password',
            role='branch_manager'
        )
        self.credit_committee = User.objects.create_user(
            username='credit_committee',
            password='password',
            role='credit_committee'
        )

        self.client_profile = Client.objects.create(
            nic_number='987654321V',
            first_name='Approval',
            last_name='Test',
            date_of_birth='1990-01-01',
            gender='F',
            phone_primary='0770000000',
            status='PENDING',
            registered_by=self.loan_officer,
        )
        ClientIncome.objects.create(
            client=self.client_profile,
            income_source='SALARY',
            monthly_income=75000,
            other_income=0,
            monthly_expenses=15000,
            existing_debt_monthly=5000,
            number_of_dependents=1,
        )

        self.loan_product = LoanProduct.objects.create(
            name='Working Capital',
            description='Approval workflow loan',
            min_amount=10000,
            max_amount=1000000,
            min_duration_months=6,
            max_duration_months=36,
            interest_rate=15.0,
        )

        self.application = LoanApplication.objects.create(
            client=self.client_profile,
            loan_product=self.loan_product,
            requested_amount=200000,
            requested_duration_months=12,
            loan_purpose='WORKING_CAPITAL',
            purpose_description='Approval workflow test',
            created_by=self.loan_officer,
            status='RISK_REVIEWED',
        )
        CashflowAssessment.objects.create(
            application=self.application,
            monthly_income=75000,
            other_income=0,
            monthly_expenses=15000,
            existing_loan_payments=5000,
            proposed_monthly_payment=8000,
            net_cashflow=52000,
            debt_to_income_ratio=0.34,
        )

    def test_risk_analyst_decision_moves_application_to_manager_review(self):
        self.client.force_authenticate(user=self.risk_analyst)

        response = self.client.post(
            f'/api/approvals/{self.application.id}/risk-decision/',
            {
                'decision': 'APPROVED',
                'comments': 'All risk criteria met',
                'ai_recommendation_followed': True,
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'MANAGER_REVIEW')
        self.assertEqual(response.data['workflow_status'], 'PENDING_MANAGER_REVIEW')

    def test_branch_manager_approval_moves_application_to_approved(self):
        self.client.force_authenticate(user=self.risk_analyst)
        self.client.post(
            f'/api/approvals/{self.application.id}/risk-decision/',
            {
                'decision': 'APPROVED',
                'comments': 'Verified risk memo and recommendation',
                'ai_recommendation_followed': True,
            },
            format='json'
        )

        self.client.force_authenticate(user=self.branch_manager)
        response = self.client.post(
            f'/api/approvals/{self.application.id}/manager-decision/',
            {
                'decision': 'APPROVED',
                'comments': 'Approved for disbursement',
                'ai_recommendation_followed': True,
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'APPROVED')
        self.assertEqual(response.data['workflow_status'], 'APPROVED')

    def test_branch_manager_escalation_to_committee(self):
        self.application.requested_amount = 750000
        self.application.save()

        self.client.force_authenticate(user=self.risk_analyst)
        self.client.post(
            f'/api/approvals/{self.application.id}/risk-decision/',
            {
                'decision': 'APPROVED',
                'comments': 'High value loan, proceed to manager review',
                'ai_recommendation_followed': True,
            },
            format='json'
        )

        self.client.force_authenticate(user=self.branch_manager)
        response = self.client.post(
            f'/api/approvals/{self.application.id}/manager-decision/',
            {
                'decision': 'ESCALATE',
                'comments': 'Requires committee review due to high amount',
                'ai_recommendation_followed': True,
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'COMMITTEE_REVIEW')
        self.assertEqual(response.data['workflow_status'], 'PENDING_COMMITTEE')

    def test_committee_vote_finalize_application(self):
        self.application.requested_amount = 750000
        self.application.save()

        self.client.force_authenticate(user=self.risk_analyst)
        self.client.post(
            f'/api/approvals/{self.application.id}/risk-decision/',
            {
                'decision': 'APPROVED',
                'comments': 'Proceed to manager review',
                'ai_recommendation_followed': True,
            },
            format='json'
        )

        self.client.force_authenticate(user=self.branch_manager)
        self.client.post(
            f'/api/approvals/{self.application.id}/manager-decision/',
            {
                'decision': 'ESCALATE',
                'comments': 'Escalate to committee',
                'ai_recommendation_followed': True,
            },
            format='json'
        )

        self.client.force_authenticate(user=self.credit_committee)
        response = self.client.post(
            f'/api/approvals/{self.application.id}/committee-vote/',
            {
                'vote': 'FOR',
                'comments': 'I support approval',
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['quorum_reached'], False)

        response = self.client.post(
            f'/api/approvals/{self.application.id}/committee-vote/',
            {
                'vote': 'FOR',
                'comments': 'Second approval vote',
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'APPROVED')
        self.assertEqual(response.data['final_decision'], 'APPROVED')
