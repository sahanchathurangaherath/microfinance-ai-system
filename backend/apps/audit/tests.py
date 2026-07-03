from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import patch, MagicMock
import json

from .models import AgentConfiguration, AgentActionLog, SystemIncident, ManualReviewCase, AgentConfigChangeLog
from .policy_engine import evaluate_and_run_agent
from .rules_fallback import run_local_rules

User = get_user_model()


class AIPolicyEngineTests(TestCase):

    def setUp(self):
        # Create an admin user for testing changed_by/triggered_by relations
        self.admin_user = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='Password123'
        )

    def test_default_configuration_creation(self):
        """Verifies that calling evaluate_and_run_agent creates configuration on the fly."""
        # Ensure configuration doesn't exist
        AgentConfiguration.objects.filter(agent_id="A2").delete()

        # Mock run_local_rules to bypass actual execution logic
        with patch('apps.audit.policy_engine.run_local_rules') as mock_rules:
            mock_rules.return_value = {
                "agent_id": "A2",
                "status": "SUCCESS",
                "confidence": 0.90,
                "output": {"risk_score": 75.0, "risk_category": "LOW"}
            }

            evaluate_and_run_agent(
                agent_id="A2",
                payload={"loan_id": 123},
                triggered_by=self.admin_user,
                input_reference="loan:123"
            )

            # Assert config was created dynamically
            cfg = AgentConfiguration.objects.get(agent_id="A2")
            self.assertTrue(cfg.llm_enabled)  # A2 risk assessment defaults to true
            self.assertFalse(cfg.is_paused)
            self.assertEqual(cfg.confidence_threshold, 0.65)

    def test_pause_kill_switch_behavior(self):
        """Verifies that when paused, the policy engine triggers local rules, logs, and creates manual review cases."""
        # Create a paused agent config
        cfg = AgentConfiguration.objects.create(
            agent_id="A3",
            llm_enabled=True,
            is_paused=True,
            pause_reason="Emergency policy update",
            confidence_threshold=0.70
        )

        payload = {"loan_id": 456, "risk_score": 45.0, "risk_category": "MEDIUM", "requested_amount": 100000.0, "monthly_income": 80000.0}

        # Trigger agent
        res = evaluate_and_run_agent(
            agent_id="A3",
            payload=payload,
            triggered_by=self.admin_user,
            input_reference="loan:456"
        )

        # 1. Output should be returned from local rules fallback
        self.assertEqual(res["agent_id"], "A3")
        self.assertEqual(res["status"], "SUCCESS")

        # 2. System incident of type A3_PAUSED should be logged
        incident = SystemIncident.objects.get(agent_id="A3", incident_type="A3_PAUSED")
        self.assertEqual(incident.severity, "PARTIAL")

        # 3. Manual review case should be created
        case = ManualReviewCase.objects.get(agent_id="A3", reference_id=456)
        self.assertEqual(case.status, "PENDING")
        self.assertIn("Agent paused by admin", case.manual_notes)

        # 4. Action log should show RULE_ONLY execution bypass
        log = AgentActionLog.objects.get(agent_id="A3", input_reference="loan:456")
        self.assertEqual(log.execution_mode, "RULE_ONLY")
        self.assertTrue(log.ai_bypassed)
        self.assertEqual(log.bypass_reason, "Agent paused by admin: Emergency policy update")

    def test_llm_disabled_fallback_behavior(self):
        """Verifies that when LLM mode is disabled, the system executes pure rules (locally or via FastAPI) and bypasses AI."""
        # Create config with LLM disabled
        AgentConfiguration.objects.create(
            agent_id="A1",
            llm_enabled=False,
            is_paused=False
        )

        payload = {"client_id": 999, "client_data": {"nic_number": "199432123V"}}

        # Mock FastAPI call and local rules
        with patch('apps.audit.policy_engine.call_fastapi_agent') as mock_fastapi:
            mock_fastapi.return_value = {
                "agent_id": "A1",
                "status": "SUCCESS",
                "confidence": 0.85,
                "output": {"data_quality_score": 85.0}
            }

            res = evaluate_and_run_agent(
                agent_id="A1",
                payload=payload,
                triggered_by=self.admin_user,
                input_reference="client:999"
            )

            # Ensure call_fastapi_agent was invoked with use_llm=False
            mock_fastapi.assert_called_once_with("A1", payload, use_llm=False)
            self.assertEqual(res["output"]["data_quality_score"], 85.0)

            # Verify action log bypass metadata
            log = AgentActionLog.objects.get(agent_id="A1", input_reference="client:999")
            self.assertEqual(log.execution_mode, "RULE_ONLY")
            self.assertTrue(log.ai_bypassed)
            self.assertEqual(log.bypass_reason, "LLM disabled by policy")

    @patch('apps.audit.policy_engine.call_fastapi_agent')
    def test_confidence_threshold_gate(self, mock_fastapi):
        """Verifies that if AI confidence falls below config threshold, the policy engine flags it for human review."""
        AgentConfiguration.objects.create(
            agent_id="A5",
            llm_enabled=True,
            confidence_threshold=0.80
        )

        # Mock low confidence AI response
        mock_fastapi.return_value = {
            "agent_id": "A5",
            "status": "SUCCESS",
            "confidence": 0.60,  # Below 0.80 threshold
            "output": {"is_suspicious": False, "fraud_risk_score": 10.0},
            "rationale": "Clear application profile."
        }

        payload = {"client_id": 888, "identity_data": {}}

        res = evaluate_and_run_agent(
            agent_id="A5",
            payload=payload,
            triggered_by=self.admin_user,
            input_reference="client:888"
        )

        # Output status should be modified to human review
        self.assertEqual(res["status"], "REQUIRES_HUMAN_REVIEW")

        # Soft review incident and review case should be created
        incident = SystemIncident.objects.get(agent_id="A5", incident_type="A5_HUMAN_REVIEW_GATE")
        self.assertEqual(incident.severity, "SOFT")
        
        case = ManualReviewCase.objects.get(agent_id="A5", reference_id=888)
        self.assertEqual(case.status, "PENDING")
        self.assertIn("AI confidence (0.6) below threshold (0.8)", case.manual_notes)

    @patch('apps.audit.policy_engine.call_fastapi_agent')
    def test_disagreement_detection_gate(self, mock_fastapi):
        """Verifies that if local rules and AI disagree, it triggers the review gate."""
        AgentConfiguration.objects.create(
            agent_id="A5",
            llm_enabled=True,
            confidence_threshold=0.60
        )

        # Mock AI output as suspicious: False (clean)
        mock_fastapi.return_value = {
            "agent_id": "A5",
            "status": "SUCCESS",
            "confidence": 0.90,
            "output": {"is_suspicious": False, "fraud_risk_score": 5.0},
            "rationale": "Looks clean."
        }

        # Mock input payload to trigger rule suspicion (Duplicate NIC weight = 40, is_suspicious=True)
        payload = {
            "client_id": 777,
            "identity_data": {"nic_duplicate_count": 2}  # Rules will calculate is_suspicious=True
        }

        res = evaluate_and_run_agent(
            agent_id="A5",
            payload=payload,
            triggered_by=self.admin_user,
            input_reference="client:777"
        )

        # Should require review since Rules (suspicious) and AI (not suspicious) disagree
        self.assertEqual(res["status"], "REQUIRES_HUMAN_REVIEW")
        self.assertIn("Rules & AI disagreed", res["rationale"])

        # Review Case should be created
        case = ManualReviewCase.objects.get(agent_id="A5", reference_id=777)
        self.assertIn("Rules & AI disagreed", case.manual_notes)

    @patch('apps.audit.policy_engine.call_fastapi_agent')
    def test_offline_ai_service_rule_fallback(self, mock_fastapi):
        """Verifies that if the FastAPI AI Service goes offline, the policy engine fails over to local rules."""
        cfg = AgentConfiguration.objects.create(
            agent_id="A2",
            llm_enabled=True,
            confidence_threshold=0.60
        )
        # Default fallback behavior is RULE_FALLBACK
        self.assertEqual(cfg.fallback_behavior, "RULE_FALLBACK")

        # Mock call_fastapi_agent to raise a connection error
        mock_fastapi.side_effect = Exception("FastAPI service connection refused")

        payload = {
            "loan_id": 111,
            "client_data": {"monthly_income": 50000},
            "loan_data": {"requested_amount": 150000}
        }

        res = evaluate_and_run_agent(
            agent_id="A2",
            payload=payload,
            triggered_by=self.admin_user,
            input_reference="loan:111"
        )

        # 1. Output should be successfully computed via local rules
        self.assertEqual(res["agent_id"], "A2")
        self.assertEqual(res["status"], "SUCCESS")
        self.assertIn("risk_score", res["output"])

        # 2. Offline Incident should be logged as HARD outage
        incident = SystemIncident.objects.get(agent_id="A2", incident_type="A2_SERVICE_OFFLINE")
        self.assertEqual(incident.severity, "HARD")

        # 3. Action log should record RULE_FALLBACK bypass details
        log = AgentActionLog.objects.get(agent_id="A2", input_reference="loan:111")
        self.assertEqual(log.execution_mode, "RULE_FALLBACK")
        self.assertTrue(log.ai_bypassed)
        self.assertIn("AI Service offline: FastAPI service connection refused", log.bypass_reason)


from rest_framework.test import APITestCase
from rest_framework import status

class AuditAPIViewsTests(APITestCase):

    def setUp(self):
        # Create users with different roles
        self.admin = User.objects.create_user(
            username='admin_api', password='password', role='admin'
        )
        self.compliance_officer = User.objects.create_user(
            username='compliance_api', password='password', role='compliance_officer'
        )
        self.risk_analyst = User.objects.create_user(
            username='risk_api', password='password', role='risk_analyst'
        )
        self.loan_officer = User.objects.create_user(
            username='loan_api', password='password', role='loan_officer'
        )
        
        # Seed an agent configuration
        self.agent_cfg = AgentConfiguration.objects.create(
            agent_id="A2",
            llm_enabled=True,
            confidence_threshold=0.65
        )

        # Seed System Incident
        self.incident = SystemIncident.objects.create(
            incident_type="A2_OUTAGE",
            severity="HARD",
            status="OPEN",
            agent_id="A2"
        )

        # Seed Manual Review Case
        self.review_case = ManualReviewCase.objects.create(
            incident=self.incident,
            agent_id="A2",
            reference_model="LoanApplication",
            reference_id=123,
            status="PENDING"
        )

    def test_agent_config_list_permissions(self):
        # 1. Without Auth or API Key -> 401
        response = self.client.get('/api/audit/agent-config/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # 2. With Admin Auth -> 200
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/audit/agent-config/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 3. With Compliance Officer Auth -> 200
        self.client.force_authenticate(user=self.compliance_officer)
        response = self.client.get('/api/audit/agent-config/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 4. With Loan Officer Auth (not allowed) -> 403
        self.client.force_authenticate(user=self.loan_officer)
        response = self.client.get('/api/audit/agent-config/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 5. With Internal API Key -> 200
        self.client.logout()
        with override_settings(AI_SERVICE_API_KEY='test-api-key'):
            response = self.client.get(
                '/api/audit/agent-config/',
                HTTP_X_API_KEY='test-api-key'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_system_incident_views_permissions(self):
        # Admin -> 200
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/audit/system/incidents/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Compliance Officer -> 200
        self.client.force_authenticate(user=self.compliance_officer)
        response = self.client.get('/api/audit/system/incidents/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Loan Officer -> 403
        self.client.force_authenticate(user=self.loan_officer)
        response = self.client.get('/api/audit/system/incidents/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Resolve Incident - Compliance Officer -> 200
        self.client.force_authenticate(user=self.compliance_officer)
        response = self.client.post(
            f'/api/audit/system/incidents/{self.incident.id}/resolve/',
            {'resolution_notes': 'Fixed'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.incident.refresh_from_db()
        self.assertEqual(self.incident.status, 'RESOLVED')

    def test_manual_review_views_permissions_and_score_optional(self):
        # 1. Queue - Compliance Officer -> 200
        self.client.force_authenticate(user=self.compliance_officer)
        response = self.client.get('/api/audit/system/manual-review/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 2. Retry - Compliance Officer -> 200
        # Mock health check for retry
        with patch('httpx.get') as mock_get:
            mock_get.return_value = MagicMock(status_code=200)
            response = self.client.post(f'/api/audit/system/manual-review/{self.review_case.id}/retry/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 3. Submit Manual Review (score optional) - Compliance Officer -> 200
        self.client.force_authenticate(user=self.compliance_officer)
        response = self.client.post(
            f'/api/audit/system/manual-review/{self.review_case.id}/submit/',
            {
                'manual_decision': 'APPROVED',
                'manual_notes': 'Override decision'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.review_case.refresh_from_db()
        self.assertEqual(self.review_case.status, 'COMPLETED')
        self.assertEqual(self.review_case.manual_decision, 'APPROVED')
        self.assertIsNone(self.review_case.manual_score)
