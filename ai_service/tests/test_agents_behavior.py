# ai_service/tests/test_agents_behavior.py
import unittest
from unittest.mock import patch, MagicMock
from datetime import date, timedelta
import sys
from pathlib import Path

# Add parent directory to sys.path so we can import services and agents
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.data_collection_agent import DataCollectionAgent
from agents.risk_assessment_agent import RiskAssessmentAgent
from agents.recommendation_agent import RecommendationAgent
from agents.monitoring_agent import MonitoringAgent
from agents.fraud_detection_agent import FraudDetectionAgent
from agents.communication_agent import CommunicationAgent
from services.guardrails import (
    validate_a1_output,
    validate_a2_output,
    validate_a3_output,
    validate_a4_llm_output,
    validate_a5_output,
    validate_a6_output,
    confidence_requires_manual_review
)

class TestAgentsBehavior(unittest.TestCase):

    def setUp(self):
        # Reset use of LLM by default
        self.a1 = DataCollectionAgent()
        self.a2 = RiskAssessmentAgent()
        self.a3 = RecommendationAgent()
        self.a4 = MonitoringAgent()
        self.a5 = FraudDetectionAgent()
        self.a6 = CommunicationAgent()

    # ==========================================
    # A1: DATA COLLECTION AGENT TESTS
    # ==========================================

    @patch("services.llm_client.call_llm")
    def test_a1_normal_input(self, mock_call):
        """Test A1 flags complete and consistent data correctly."""
        mock_call.return_value = ({
            "data_quality_score": 95.0,
            "missing_critical_fields": [],
            "consistency_flags": [],
            "fraud_signals": [],
            "confidence": 0.95,
            "rationale": "Client KYC data is completely consistent."
        }, {"model_used": "qwen3:8b"})

        input_data = {
            "client_id": 101,
            "client_data": {
                "nic_number": "199012345678",
                "first_name": "Sahan",
                "last_name": "Herath",
                "date_of_birth": "1990-01-01",
                "phone_primary": "+94771234567",
                "monthly_income": 80000
            },
            "kyc_data": {
                "address_verified": True,
                "income_verified": True,
                "id_document_uploaded": True,
                "income_document_uploaded": True
            }
        }
        # Enable LLM
        with patch("agents.data_collection_agent.USE_LLM", True):
            res = self.a1.run(input_data)
        
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["confidence"], 0.95)
        self.assertEqual(res["output"]["data_quality_score"], 95.0)
        self.assertEqual(res["output"]["missing_critical_fields"], [])

    @patch("services.llm_client.call_llm")
    def test_a1_adversarial_inconsistent_input(self, mock_call):
        """Test A1 flags incomplete/inconsistent data correctly under adversarial input."""
        mock_call.return_value = ({
            "data_quality_score": 40.0,
            "missing_critical_fields": ["nic_number"],
            "consistency_flags": ["Income vs business age mismatch"],
            "fraud_signals": ["NIC document is missing"],
            "confidence": 0.85,
            "rationale": "NIC number is missing. Stated business age (10 years) conflicts with low income."
        }, {"model_used": "qwen3:8b"})

        input_data = {
            "client_id": 102,
            "client_data": {
                "first_name": "Adversarial",
                "last_name": "Test",
                "monthly_income": 1000,
                "years_in_operation": 10
            },
            "kyc_data": {
                "id_document_uploaded": False
            }
        }
        with patch("agents.data_collection_agent.USE_LLM", True):
            res = self.a1.run(input_data)

        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["output"]["data_quality_score"], 40.0)
        self.assertIn("nic_number", res["output"]["missing_critical_fields"])
        self.assertIn("Income vs business age mismatch", res["output"]["consistency_flags"])

    # ==========================================
    # A2: RISK ASSESSMENT AGENT TESTS
    # ==========================================

    @patch("services.llm_client.call_llm")
    def test_a2_risk_score_and_rationale(self, mock_call):
        """Test A2 risk assessment returns 0-100 score and full rationale."""
        mock_call.return_value = ({
            "risk_score": 75.0,
            "risk_category": "LOW",
            "confidence": 0.90,
            "factor_scores": {
                "dti_score": 20,
                "lti_score": 15,
                "kyc_score": 15,
                "income_stability_score": 10,
                "repayment_history_score": 10,
                "dependents_score": 5
            },
            "default_signals": [],
            "required_action": "LOAN_OFFICER_REVIEW",
            "ai_rationale": "Client exhibits low DTI (25%) and stable income stream. Repayment history is positive."
        }, {"model_used": "qwen3:8b"})

        input_data = {
            "loan_id": 201,
            "client_data": {"monthly_income": 75000, "years_in_operation": 4, "data_quality_score": 90},
            "loan_data": {"requested_amount": 150000, "requested_duration_months": 12, "debt_to_income_ratio": 0.25},
            "repayment_history": {"previous_loans_count": 2, "missed_payments": 0}
        }
        with patch("agents.risk_assessment_agent.USE_LLM", True):
            res = self.a2.run(input_data)

        self.assertEqual(res["status"], "SUCCESS")
        self.assertTrue(0 <= res["output"]["risk_score"] <= 100)
        self.assertEqual(res["output"]["risk_score"], 75.0)
        # Rationale must not be empty or bare number
        self.assertTrue(len(res["rationale"]) > 20)
        self.assertIn("stable income", res["rationale"].lower())

    # ==========================================
    # A3: RECOMMENDATION AGENT TESTS
    # ==========================================

    @patch("services.llm_client.call_llm")
    def test_a3_recommendation_and_reasoning_tied_to_a2(self, mock_call):
        """Test A3 outputs valid recommendation type tied to A2 score."""
        mock_call.return_value = ({
            "recommendation_type": "RECOMMEND_REJECTION",
            "recommended_amount": None,
            "recommended_duration_months": 12,
            "explanation": "Risk score of 25/100 is critically low due to multiple missed payments.",
            "reasons": ["Critical risk score", "Repayment history warnings"],
            "alternative_product_suggestion": None,
            "confidence": 0.85
        }, {"model_used": "qwen3:8b"})

        input_data = {
            "loan_id": 301,
            "risk_score": 25.0,
            "risk_category": "HIGH",
            "ai_rationale": "Multiple missed payments and high DTI.",
            "default_signals": ["3 missed payments", "DTI exceeds 60%"],
            "kyc_score": 85,
            "requested_amount": 200000,
            "monthly_income": 40000,
            "requested_duration_months": 12
        }
        with patch("agents.recommendation_agent.USE_LLM", True):
            res = self.a3.run(input_data)

        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["output"]["recommendation_type"], "RECOMMEND_REJECTION")
        self.assertIn("Risk score of 25/100", res["rationale"])

    # ==========================================
    # A4: MONITORING AGENT TESTS
    # ==========================================

    def test_a4_boundary_dates(self):
        """Test A4 correctly classifies overdue installments at boundary dates."""
        today = date(2026, 7, 2)
        
        # 1 day overdue (due date: 2026-07-01)
        inst_1d = {
            "installment_id": 401,
            "installment_number": 1,
            "due_date": str(today - timedelta(days=1)),
            "amount_due": 5000.0,
            "outstanding": 5000.0,
            "status": "UNPAID"
        }
        # 7 days overdue (due date: 2026-06-25)
        inst_7d = {
            "installment_id": 402,
            "installment_number": 2,
            "due_date": str(today - timedelta(days=7)),
            "amount_due": 5000.0,
            "outstanding": 5000.0,
            "status": "UNPAID"
        }
        # 8 days overdue (due date: 2026-06-24)
        inst_8d = {
            "installment_id": 403,
            "installment_number": 3,
            "due_date": str(today - timedelta(days=8)),
            "amount_due": 5000.0,
            "outstanding": 5000.0,
            "status": "UNPAID"
        }
        # 30 days overdue (due date: 2026-06-02)
        inst_30d = {
            "installment_id": 404,
            "installment_number": 4,
            "due_date": str(today - timedelta(days=30)),
            "amount_due": 5000.0,
            "outstanding": 5000.0,
            "status": "UNPAID"
        }
        # 31 days overdue (due date: 2026-06-01)
        inst_31d = {
            "installment_id": 405,
            "installment_number": 5,
            "due_date": str(today - timedelta(days=31)),
            "amount_due": 5000.0,
            "outstanding": 5000.0,
            "status": "UNPAID"
        }

        input_data = {
            "loans": [
                {
                    "loan_id": 44,
                    "loan_number": "L-999",
                    "installments": [inst_1d, inst_7d, inst_8d, inst_30d, inst_31d]
                }
            ],
            "today": str(today)
        }

        # A4 runs rule-based overdue scan
        res = self.a4.run(input_data)
        self.assertEqual(res["status"], "SUCCESS")
        
        cases = res["output"]["overdue_cases"]
        self.assertEqual(len(cases), 5)

        # Map by installment_id for assertion
        cases_map = {c["installment_id"]: c for c in cases}

        # Check 1 day overdue
        self.assertEqual(cases_map[401]["days_overdue"], 1)
        self.assertEqual(cases_map[401]["bucket"], "BUCKET_1_7")
        self.assertEqual(cases_map[401]["severity"], "EARLY_OVERDUE")
        self.assertEqual(cases_map[401]["recommended_action"], "SEND_REMINDER")

        # Check 7 days overdue
        self.assertEqual(cases_map[402]["days_overdue"], 7)
        self.assertEqual(cases_map[402]["bucket"], "BUCKET_1_7")
        self.assertEqual(cases_map[402]["severity"], "EARLY_OVERDUE")
        self.assertEqual(cases_map[402]["recommended_action"], "SEND_REMINDER")

        # Check 8 days overdue
        self.assertEqual(cases_map[403]["days_overdue"], 8)
        self.assertEqual(cases_map[403]["bucket"], "BUCKET_8_30")
        self.assertEqual(cases_map[403]["severity"], "WARNING")
        self.assertEqual(cases_map[403]["recommended_action"], "COLLECTIONS_CONTACT")

        # Check 30 days overdue
        self.assertEqual(cases_map[404]["days_overdue"], 30)
        self.assertEqual(cases_map[404]["bucket"], "BUCKET_8_30")
        self.assertEqual(cases_map[404]["severity"], "WARNING")
        self.assertEqual(cases_map[404]["recommended_action"], "COLLECTIONS_CONTACT")

        # Check 31 days overdue
        self.assertEqual(cases_map[405]["days_overdue"], 31)
        self.assertEqual(cases_map[405]["bucket"], "BUCKET_OVER_30")
        self.assertEqual(cases_map[405]["severity"], "CRITICAL")
        self.assertEqual(cases_map[405]["recommended_action"], "ESCALATE_TO_MANAGER")

    # ==========================================
    # A5: FRAUD DETECTION AGENT TESTS
    # ==========================================

    def test_a5_rule_layer_signals(self):
        """Test that A5 rule-layer signals fire correctly."""
        input_data = {
            "client_id": 501,
            "loan_id": 5001,
            "identity_data": {
                "nic_duplicate_count": 2,      # Should trigger DUPLICATE_NIC (+40)
                "phone_shared_count": 3,        # Should trigger SHARED_PHONE (+15)
                "address_shared_count": 3       # Should trigger SHARED_ADDRESS (+10)
            },
            "application_data": {
                "applications_last_30_days": 4, # Should trigger RAPID_APPLICATIONS (+20)
                "requested_amount": 600000.0,   # Should trigger ROUND_AMOUNT_PATTERN (+5)
                "monthly_income": 8000.0        # Annual = 96000. 600000 > 5x annual. Trigger UNUSUAL_AMOUNT (+20)
            },
            "payment_data": {
                "reversals_last_7_days": 2      # Should trigger PAYMENT_REVERSALS (+25)
            },
            "kyc_data": {
                "completion_time_minutes": 5    # Should trigger KYC_RUSH (+10)
            }
        }
        
        # Rule score = 40 + 15 + 10 + 20 + 20 + 5 + 25 + 10 = 145 -> Clamped to 100.0
        with patch("agents.fraud_detection_agent.USE_LLM", False):
            res = self.a5.run(input_data)
        
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["output"]["fraud_risk_score"], 100.0)
        self.assertEqual(res["output"]["severity"], "CRITICAL")
        
        signals_types = [s["type"] for s in res["output"]["signals"]]
        self.assertIn("DUPLICATE_NIC", signals_types)
        self.assertIn("SHARED_PHONE", signals_types)
        self.assertIn("SHARED_ADDRESS", signals_types)
        self.assertIn("RAPID_APPLICATIONS", signals_types)
        self.assertIn("UNUSUAL_AMOUNT", signals_types)
        self.assertIn("ROUND_AMOUNT_PATTERN", signals_types)
        self.assertIn("PAYMENT_REVERSALS", signals_types)
        self.assertIn("KYC_RUSH", signals_types)

    @patch("services.llm_client.call_llm")
    def test_a5_adversarial_severity_lowering(self, mock_call):
        """
        Adversarial: Attempt to construct a case where LLM lowers severity,
        and confirm if the implementation successfully prevents it or violates the rule.
        """
        # Rule-based score triggers: DUPLICATE_NIC (40) + RAPID_APPLICATIONS (20) + PAYMENT_REVERSALS (25) = 85.0 (CRITICAL)
        # LLM returns a very low fraud score: 10.0 (LOW)
        mock_call.return_value = ({
            "fraud_risk_score": 10.0,
            "severity": "LOW",
            "prosecutor_findings": ["duplicate NIC found"],
            "defense_findings": ["mistyped numbers", "valid reversals"],
            "verdict_rationale": "Clear innocent explanation for all signals.",
            "confidence": 0.90,
            "investigation_focus": "NIC check"
        }, {"model_used": "qwen3:8b"})

        input_data = {
            "client_id": 502,
            "loan_id": 5002,
            "identity_data": {"nic_duplicate_count": 1},
            "application_data": {"applications_last_30_days": 3},
            "payment_data": {"reversals_last_7_days": 2},
            "kyc_data": {}
        }

        with patch("agents.fraud_detection_agent.USE_LLM", True):
            res = self.a5.run(input_data)
        
        # Audit calculation:
        # Rule score = 85.0
        # LLM score = 10.0
        # Final score = (85 * 0.5) + (10 * 0.5) = 47.5
        # 47.5 severity = MEDIUM
        # Rule score severity was CRITICAL (85.0), final severity is MEDIUM (47.5).
        # We check if the severity was lowered.
        rule_score = 85.0
        rule_severity = "CRITICAL"
        final_severity = res["output"]["severity"]
        
        print(f"\n[A5 AUDIT] Rule severity: {rule_severity} (score: {rule_score})")
        print(f"[A5 AUDIT] Final severity after LLM: {final_severity} (score: {res['output']['fraud_risk_score']})")
        
        # Assert to verify if it violates the non-negotiable rule: "LLM layer may only raise severity, never lower it"
        # If final_severity is lower than rule_severity, it violates the rule!
        severity_hierarchy = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        is_lowered = severity_hierarchy[final_severity] < severity_hierarchy[rule_severity]
        
        # We record the assertion. If it fails, the rule is violated.
        # To satisfy "confirm it never does", we assert is_lowered is False.
        # This test will fail if it DOES lower severity, thus highlighting the violation.
        self.assertFalse(is_lowered, "CRITICAL VIOLATION: A5 LLM layer lowered the fraud severity!")

    # ==========================================
    # A6: COMMUNICATION AGENT TESTS
    # ==========================================

    @patch("services.llm_client.call_llm")
    def test_a6_multilingual_drafts(self, mock_call):
        """Test A6 drafts and multilingual outputs (English/Sinhala)."""
        mock_call.return_value = ({
            "drafts": [
                {
                    "channel": "SMS",
                    "body": "හිතවත් ගනුදෙනුකරුණි, ඔබගේ වාරිකය ගෙවීමට මතක් කරමු.",
                    "character_count": 52
                }
            ],
            "tone_applied": "empathetic",
            "language_used": "si",
            "confidence": 0.85
        }, {"model_used": "qwen3:8b"})

        input_data = {
            "comm_type": "REPAYMENT_REMINDER",
            "channels": ["SMS"],
            "context": {
                "client_name": "Sahan Herath",
                "amount": 5000,
                "due_date": "2026-07-05",
                "loan_number": "L-101",
                "preferred_language": "si"
            }
        }
        with patch("agents.communication_agent.USE_LLM", True):
            res = self.a6.run(input_data)

        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["output"]["language_used"], "si")
        self.assertTrue(len(res["output"]["drafts"]) > 0)
        self.assertEqual(res["output"]["drafts"][0]["channel"], "SMS")
        self.assertIn("හිතවත්", res["output"]["drafts"][0]["body"])

    # ==========================================
    # CONFIDENCE & GUARDRAILS TESTS
    # ==========================================

    @patch("services.llm_client.call_llm")
    def test_confidence_escalation_triggers_for_all_agents(self, mock_call):
        """Confirm confidence < 0.65 triggers escalation for every agent, not just some."""
        # Setup low confidence return
        mock_call.return_value = ({
            "data_quality_score": 80.0,
            "risk_score": 80.0,
            "risk_category": "LOW",
            "recommendation_type": "RECOMMEND_APPROVAL",
            "severity": "LOW",
            "fraud_risk_score": 10.0,
            "drafts": [{"channel": "SMS", "body": "Draft msg"}],
            "confidence": 0.50,            # < 0.65
            "rationale": "Unsure about client status.",
            "ai_rationale": "Unsure.",
            "explanation": "Unsure.",
            "verdict_rationale": "Unsure."
        }, {"model_used": "qwen3:8b"})

        agents_to_test = [
            ("A1", self.a1, {"client_id": 101, "client_data": {}, "kyc_data": {}}, "A1_USE_LLM"),
            ("A2", self.a2, {
                "loan_id": 201, "client_data": {}, "loan_data": {}, "repayment_history": {}
            }, "A2_USE_LLM"),
            ("A3", self.a3, {
                "loan_id": 301, "risk_score": 80, "risk_category": "LOW", "requested_amount": 1000,
                "monthly_income": 5000, "requested_duration_months": 12
            }, "A3_USE_LLM"),
            # Note: A4, A5, A6 will be tested to see if they escalate on LLM confidence < 0.65
            ("A5", self.a5, {
                "client_id": 501, "loan_id": 5001, "identity_data": {"nic_duplicate_count": 1}
            }, "A5_USE_LLM"),
            ("A6", self.a6, {
                "comm_type": "SMS", "context": {}, "channels": ["SMS"]
            }, "A6_USE_LLM")
        ]

        print("\n[CONFIDENCE AUDIT] Testing confidence < 0.65 escalation:")
        failures = []
        for name, agent, payload, patch_var in agents_to_test:
            with patch(f"agents.{agent.__class__.__module__.split('.')[-1]}.USE_LLM", True):
                res = agent.run(payload)
                
            status = res.get("status")
            confidence = res.get("confidence", 1.0)
            print(f"Agent {name} output status: {status}, returned confidence: {confidence}")
            
            # If status is not REQUIRES_HUMAN_REVIEW or similar low confidence format, it is a failure
            # Standard escalation status in BaseAgent is REQUIRES_HUMAN_REVIEW
            if status != "REQUIRES_HUMAN_REVIEW":
                failures.append(name)

        self.assertEqual(failures, [], f"CRITICAL VIOLATION: Agents {failures} failed to escalate on confidence < 0.65!")

    def test_guardrails_reject_malformed_outputs(self):
        """Confirm guardrails.py rejects malformed AI output rather than passing it through."""
        # A1 malformed: missing rationale
        self.assertFalse(validate_a1_output({"data_quality_score": 85.0})[0])
        # A1 malformed: score out of range
        self.assertFalse(validate_a1_output({"data_quality_score": 105.0, "rationale": "ok"})[0])
        
        # A2 malformed: missing risk_category
        self.assertFalse(validate_a2_output({"risk_score": 50, "confidence": 0.8, "ai_rationale": "ok"})[0])
        
        # A3 malformed: invalid recommendation type
        self.assertFalse(validate_a3_output({"recommendation_type": "APPROVED", "explanation": "ok"})[0])

        # A4 malformed: default probability out of range
        self.assertFalse(validate_a4_llm_output({"predicted_default_probability": 1.5, "behavioral_pattern_label": "UNKNOWN"})[0])

        # A5 malformed: prohibited word in rationale
        self.assertFalse(validate_a5_output({
            "fraud_risk_score": 10.0,
            "severity": "LOW",
            "verdict_rationale": "We should freeze the client account."
        })[0])

        # A6 malformed: prohibited word in draft
        self.assertFalse(validate_a6_output({
            "drafts": [{"channel": "SMS", "body": "We will blacklist you if you do not pay."}]
        })[0])


if __name__ == "__main__":
    unittest.main()
