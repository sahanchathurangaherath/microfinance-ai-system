from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import (
    AuditLog, AgentActionLog, HumanDecisionLog, LoginAttempt,
    AIServiceStatus, SystemIncident, ManualReviewCase
)
from .serializers import (
    AuditLogSerializer, AgentActionLogSerializer,
    HumanDecisionLogSerializer, LoginAttemptSerializer,
    SystemIncidentSerializer, ManualReviewCaseSerializer,
    AIServiceStatusSerializer
)
from .utils import log_action
from apps.users.permissions import IsAdmin, IsBranchManager, IsAdminOrBranchManager, IsRiskAnalyst, IsComplianceOfficer
import httpx
from django.conf import settings
from django.utils import timezone


class AuditLogListView(generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [IsComplianceOfficer]

    def get_queryset(self):
        qs = AuditLog.objects.all()
        action_type = self.request.query_params.get('action_type')
        user_id = self.request.query_params.get('user_id')
        model_name = self.request.query_params.get('model_name')
        date_from = self.request.query_params.get('from')
        date_to = self.request.query_params.get('to')

        if action_type:
            qs = qs.filter(action_type=action_type)
        if user_id:
            qs = qs.filter(user_id=user_id)
        if model_name:
            qs = qs.filter(model_name__icontains=model_name)
        if date_from:
            qs = qs.filter(timestamp__date__gte=date_from)
        if date_to:
            qs = qs.filter(timestamp__date__lte=date_to)

        return qs


class AgentActionLogListView(generics.ListAPIView):
    serializer_class = AgentActionLogSerializer
    permission_classes = [IsComplianceOfficer]

    def get_queryset(self):
        qs = AgentActionLog.objects.all()
        agent_id = self.request.query_params.get('agent_id')
        if agent_id:
            qs = qs.filter(agent_id=agent_id)
        return qs


class HumanDecisionLogListView(generics.ListAPIView):
    serializer_class = HumanDecisionLogSerializer
    permission_classes = [IsComplianceOfficer]

    def get_queryset(self):
        qs = HumanDecisionLog.objects.all()
        decision_type = self.request.query_params.get('decision_type')
        followed_ai = self.request.query_params.get('followed_ai')
        if decision_type:
            qs = qs.filter(decision_type=decision_type)
        if followed_ai is not None:
            qs = qs.filter(followed_ai=(followed_ai.lower() == 'true'))
        return qs


class LoginAttemptListView(generics.ListAPIView):
    serializer_class = LoginAttemptSerializer
    permission_classes = [IsComplianceOfficer]

    def get_queryset(self):
        qs = LoginAttempt.objects.all()
        success = self.request.query_params.get('success')
        if success is not None:
            qs = qs.filter(success=(success.lower() == 'true'))
        return qs


class MyAuditTrailView(APIView):
    """Any logged-in user can view their own audit trail."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logs = AuditLog.objects.filter(user=request.user)[:50]
        return Response(AuditLogSerializer(logs, many=True).data)


class AIHealthCheckView(APIView):
    """
    Pings the FastAPI AI service and updates AIServiceStatus.
    Safe to call frequently — designed to be polled every 60 seconds.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            response = httpx.get(
                f"{settings.AI_SERVICE_URL}/health",
                headers={"x-api-key": settings.AI_SERVICE_API_KEY},
                timeout=5.0
            )
            is_up = response.status_code == 200
        except Exception as e:
            is_up = False

        status_obj, _ = AIServiceStatus.objects.get_or_create(pk=1)

        if is_up:
            was_offline = status_obj.status != 'ONLINE'
            status_obj.status = 'ONLINE'
            status_obj.consecutive_failures = 0
            status_obj.last_online = timezone.now()
            status_obj.save()
            if was_offline:
                from .ai_failure_handler import handle_ai_recovery
                queued = handle_ai_recovery()
                return Response({
                    "ai_service": "ONLINE",
                    "recovered": True,
                    "queued_for_retry": queued,
                    "manual_mode": False
                })
        else:
            status_obj.consecutive_failures += 1
            if status_obj.consecutive_failures >= 3:
                status_obj.status = 'OFFLINE'
                status_obj.manual_mode_active = True
            else:
                status_obj.status = 'DEGRADED'
            status_obj.save()

        return Response({
            "ai_service": status_obj.status,
            "manual_mode": status_obj.manual_mode_active,
            "consecutive_failures": status_obj.consecutive_failures,
            "last_online": status_obj.last_online,
        })


class EnableManualModeView(APIView):
    """Branch Manager manually activates manual mode."""
    permission_classes = [IsBranchManager]

    def post(self, request):
        status_obj, _ = AIServiceStatus.objects.get_or_create(pk=1)
        status_obj.manual_mode_active = True
        status_obj.notes = request.data.get("reason", "Manually enabled by manager")
        status_obj.save()

        log_action(
            user=request.user,
            action_type='SYSTEM',
            model_name='AIServiceStatus',
            object_id=str(status_obj.pk),
            description="Manual mode enabled by Branch Manager",
            request=request
        )

        return Response({
            "message": "Manual mode enabled.",
            "manual_mode": True
        })


class DisableManualModeView(APIView):
    """Branch Manager deactivates manual mode after AI recovery."""
    permission_classes = [IsBranchManager]

    def post(self, request):
        status_obj, _ = AIServiceStatus.objects.get_or_create(pk=1)
        status_obj.manual_mode_active = False
        status_obj.notes = "Manually disabled — AI service confirmed healthy"
        status_obj.save()

        log_action(
            user=request.user,
            action_type='SYSTEM',
            model_name='AIServiceStatus',
            object_id=str(status_obj.pk),
            description="Manual mode disabled by Branch Manager",
            request=request
        )

        return Response({
            "message": "Manual mode disabled. AI agents are active.",
            "manual_mode": False
        })


class SystemIncidentListView(generics.ListAPIView):
    serializer_class = SystemIncidentSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = SystemIncident.objects.all()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class ResolveIncidentView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, incident_id):
        try:
            incident = SystemIncident.objects.get(pk=incident_id)
        except SystemIncident.DoesNotExist:
            return Response({"error": "Incident not found"}, status=404)

        incident.status = 'RESOLVED'
        incident.resolved_at = timezone.now()
        incident.resolved_by = request.user
        incident.resolution_notes = request.data.get("resolution_notes", "")
        incident.save()

        return Response({"message": "Incident resolved.", "incident_id": incident.id})


class ManualReviewQueueView(generics.ListAPIView):
    """Shows all pending manual review cases when AI is down."""
    serializer_class = ManualReviewCaseSerializer
    permission_classes = [IsAdminOrBranchManager]

    def get_queryset(self):
        return ManualReviewCase.objects.filter(
            status__in=['PENDING', 'IN_PROGRESS']
        )


class SubmitManualReviewView(APIView):
    """
    Officer submits a manual risk score and decision when AI is unavailable.
    This substitutes the A2 output and moves the application forward.
    """
    permission_classes = [IsRiskAnalyst]

    def post(self, request, case_id):
        try:
            case = ManualReviewCase.objects.get(pk=case_id)
        except ManualReviewCase.DoesNotExist:
            return Response({"error": "Manual review case not found."}, status=404)

        manual_score = request.data.get("manual_score")
        manual_decision = request.data.get("manual_decision")
        manual_notes = request.data.get("manual_notes", "")

        if manual_score is None or not manual_decision:
            return Response(
                {"error": "manual_score and manual_decision are required."},
                status=400
            )

        case.manual_score = float(manual_score)
        case.manual_decision = manual_decision
        case.manual_notes = manual_notes
        case.status = 'COMPLETED'
        case.assigned_to = request.user
        case.completed_at = timezone.now()
        case.save()

        # Log the manual decision
        log_action(
            user=request.user,
            action_type='OVERRIDE',
            model_name=case.reference_model,
            object_id=str(case.reference_id),
            description=(
                f"Manual review submitted by {request.user.get_full_name()} "
                f"(AI was unavailable). Score: {manual_score}. Decision: {manual_decision}."
            ),
            request=request,
            extra_data={
                "manual_score": manual_score,
                "manual_decision": manual_decision,
                "agent_id": case.agent_id
            }
        )

        return Response({
            "message": "Manual review submitted successfully.",
            "case_id": case.id,
            "manual_score": case.manual_score,
            "manual_decision": case.manual_decision,
        })


class RetryAIRequestView(APIView):
    """
    After AI recovery, retry a previously failed agent call.
    Looks up the manual review case and re-triggers the correct agent.
    """
    permission_classes = [IsAdminOrBranchManager]

    def post(self, request, case_id):
        try:
            case = ManualReviewCase.objects.get(pk=case_id)
        except ManualReviewCase.DoesNotExist:
            return Response({"error": "Case not found."}, status=404)

        # Check AI is up before retrying
        try:
            health = httpx.get(
                f"{settings.AI_SERVICE_URL}/health",
                timeout=5.0
            )
            if health.status_code != 200:
                return Response(
                    {"error": "AI service is still unavailable. Cannot retry."},
                    status=503
                )
        except Exception:
            return Response(
                {"error": "AI service is still unreachable."},
                status=503
            )

        case.status = 'AI_RETRY_QUEUED'
        case.save()

        return Response({
            "message": (
                f"Case #{case.id} queued for AI retry. "
                f"Trigger the appropriate AI endpoint for "
                f"{case.reference_model}#{case.reference_id}."
            ),
            "agent_id": case.agent_id,
            "reference_model": case.reference_model,
            "reference_id": case.reference_id,
        })