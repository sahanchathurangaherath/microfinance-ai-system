from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django.utils import timezone
from datetime import timedelta
import httpx
import json
from django.conf import settings
from django.db.models import Count

from .models import FraudAlert, FraudInvestigation, ComplianceAction
from .serializers import FraudAlertSerializer, FraudInvestigationSerializer, ComplianceActionSerializer
from apps.audit.utils import log_agent_action
from apps.clients.models import Client
from apps.loans.models import LoanApplication
from apps.users.permissions import IsComplianceOfficer, IsAdmin


class TriggerFraudCheckView(APIView):
    """Runs A5 on a client and/or application."""
    permission_classes = [IsComplianceOfficer]

    def post(self, request):
        client_id = request.data.get("client_id")
        loan_id = request.data.get("loan_id")

        # Build identity signals
        identity_data = {}
        if client_id:
            try:
                client = Client.objects.get(pk=client_id)
                identity_data = {
                    "nic_duplicate_count": Client.objects.filter(
                        nic_number=client.nic_number
                    ).exclude(pk=client_id).count(),
                    "phone_shared_count": Client.objects.filter(
                        phone_primary=client.phone_primary
                    ).exclude(pk=client_id).count(),
                }
            except Client.DoesNotExist:
                pass

        # Build application data
        application_data = {}
        if loan_id:
            try:
                app = LoanApplication.objects.get(pk=loan_id)
                recent_apps = LoanApplication.objects.filter(
                    client=app.client,
                    created_at__gte=timezone.now() - timedelta(days=30)
                ).count()
                income = getattr(app.client, 'income', None)
                application_data = {
                    "requested_amount": float(app.requested_amount),
                    "monthly_income": float(income.monthly_income) if income else 0,
                    "applications_last_30_days": recent_apps,
                }
            except LoanApplication.DoesNotExist:
                pass

        payload = {
            "client_id": client_id,
            "loan_id": loan_id,
            "identity_data": identity_data,
            "application_data": application_data,
            "payment_data": {},
            "kyc_data": {},
        }

        # Call A5 via Policy Engine
        from apps.audit.policy_engine import evaluate_and_run_agent
        ai_result = evaluate_and_run_agent(
            agent_id="A5",
            payload=payload,
            triggered_by=request.user,
            input_reference=f"client:{client_id}|loan:{loan_id}",
            trigger_type="manual"
        )

        output = ai_result.get("output", {})

        # Create FraudAlert if suspicious
        alert = None
        if output.get("is_suspicious"):
            signals = output.get("signals", [])
            primary_type = signals[0]["type"] if signals else "BEHAVIORAL"

            # Map signal type to alert type
            type_map = {
                "DUPLICATE_NIC": "DUPLICATE_IDENTITY",
                "SHARED_PHONE": "DUPLICATE_IDENTITY",
                "RAPID_APPLICATIONS": "APPLICATION_PATTERN",
                "UNUSUAL_AMOUNT": "UNUSUAL_AMOUNT",
                "PAYMENT_REVERSALS": "PAYMENT_ANOMALY",
                "KYC_RUSH": "KYC_ANOMALY",
            }
            alert_type = type_map.get(primary_type, "BEHAVIORAL")

            alert = FraudAlert.objects.create(
                client_id=client_id,
                application_id=loan_id,
                alert_type=alert_type,
                severity=output.get("severity", "MEDIUM"),
                fraud_risk_score=output.get("fraud_risk_score", 0),
                ai_rationale=ai_result.get("rationale", ""),
                detected_signals=output.get("signals", []),
                ai_confidence=ai_result.get("confidence", 0),
                prosecutor_findings=output.get("prosecutor_findings", []),
                defense_findings=output.get("defense_findings", []),
                investigation_focus=output.get("investigation_focus", ""),
            )

        return Response({
            "fraud_risk_score": output.get("fraud_risk_score"),
            "severity": output.get("severity"),
            "is_suspicious": output.get("is_suspicious"),
            "alert_id": alert.id if alert else None,
            "recommended_action": output.get("recommended_action"),
            "agent_response": ai_result
        })


class FraudAlertListView(generics.ListAPIView):
    serializer_class = FraudAlertSerializer
    permission_classes = [IsComplianceOfficer]

    def get_queryset(self):
        qs = FraudAlert.objects.all()
        severity = self.request.query_params.get('severity')
        status_filter = self.request.query_params.get('status')
        is_resolved = self.request.query_params.get('is_resolved')
        
        if severity:
            qs = qs.filter(severity=severity)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if is_resolved:
            resolved_statuses = ['CLEARED', 'CONFIRMED', 'CLOSED']
            if is_resolved.lower() == 'true':
                qs = qs.filter(status__in=resolved_statuses)
            elif is_resolved.lower() == 'false':
                qs = qs.exclude(status__in=resolved_statuses)
        return qs


class FraudAlertDetailView(generics.RetrieveAPIView):
    queryset = FraudAlert.objects.all()
    serializer_class = FraudAlertSerializer
    permission_classes = [IsComplianceOfficer]


class OpenInvestigationView(APIView):
    """Compliance Officer opens a formal investigation on an alert."""
    permission_classes = [IsComplianceOfficer]

    def post(self, request, alert_id):
        try:
            alert = FraudAlert.objects.get(pk=alert_id)
        except FraudAlert.DoesNotExist:
            return Response({"error": "Alert not found."}, status=404)

        if alert.status != 'OPEN':
            return Response(
                {"error": f"Alert is already {alert.status}."},
                status=400
            )

        investigation, created = FraudInvestigation.objects.get_or_create(
            alert=alert,
            defaults={"investigator": request.user}
        )

        alert.status = 'UNDER_INVESTIGATION'
        alert.assigned_to = request.user
        alert.save()

        return Response({
            "message": "Investigation opened.",
            "alert_id": alert.id,
            "investigation_id": investigation.id
        })


class CloseAlertView(APIView):
    """Compliance Officer closes an alert after investigation."""
    permission_classes = [IsComplianceOfficer]

    def post(self, request, alert_id):
        try:
            alert = FraudAlert.objects.get(pk=alert_id)
        except FraudAlert.DoesNotExist:
            return Response({"error": "Alert not found."}, status=404)

        outcome = request.data.get("outcome")
        findings = request.data.get("findings", "")
        action_type = request.data.get("compliance_action")
        action_reason = request.data.get("action_reason", "")

        if outcome not in ['CLEARED', 'CONFIRMED', 'INCONCLUSIVE']:
            return Response(
                {"error": "outcome must be CLEARED, CONFIRMED, or INCONCLUSIVE."},
                status=400
            )

        # Update investigation
        try:
            inv = alert.investigation
            inv.outcome = outcome
            inv.findings = findings
            inv.completed_at = timezone.now()
            inv.save()
        except FraudInvestigation.DoesNotExist:
            pass

        # Record compliance action
        if action_type:
            ComplianceAction.objects.create(
                alert=alert,
                action_type=action_type,
                authorized_by=request.user,
                reason=action_reason,
            )

        if outcome == 'CONFIRMED':
            alert.status = 'CONFIRMED'
        elif outcome == 'CLEARED':
            alert.status = 'CLEARED'
        else:  # INCONCLUSIVE
            alert.status = 'CLOSED'
        
        alert.investigation_notes = findings
        alert.save()

        return Response({
            "message": f"Alert closed. Outcome: {outcome}.",
            "alert_status": alert.status
        })