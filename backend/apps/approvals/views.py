from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django.utils import timezone
from django.conf import settings

from .models import ApprovalWorkflow, ApprovalDecision, CommitteeDecision
from .serializers import ApprovalWorkflowSerializer, ApprovalDecisionSerializer
from apps.loans.models import LoanApplication
from apps.loans.utils import log_status_change
from apps.users.permissions import IsRiskAnalyst, IsBranchManager, IsCreditCommittee, IsAdmin
from apps.audit.utils import log_action, log_human_decision


#COMMITTEE THRESHOLD 
COMMITTEE_THRESHOLD = 500000  # LKR — applications above this go to committee


def _get_or_create_workflow(application):
    workflow, created = ApprovalWorkflow.objects.get_or_create(
        application=application,
        defaults={
            "requires_committee": float(application.requested_amount) >= COMMITTEE_THRESHOLD
        }
    )
    return workflow


# PENDING QUEUES 
class PendingRiskReviewView(generics.ListAPIView):
    """Risk Analyst sees all applications waiting for their review."""
    serializer_class = ApprovalWorkflowSerializer
    permission_classes = [IsRiskAnalyst]

    def get_queryset(self):
        return ApprovalWorkflow.objects.filter(
            status='PENDING_RISK_REVIEW'
        ).select_related('application', 'application__client', 'application__risk_assessment')


class PendingManagerReviewView(generics.ListAPIView):
    """Branch Manager sees all applications waiting for their review."""
    serializer_class = ApprovalWorkflowSerializer
    permission_classes = [IsBranchManager]

    def get_queryset(self):
        return ApprovalWorkflow.objects.filter(
            status='PENDING_MANAGER_REVIEW'
        ).select_related('application', 'application__client')


class PendingCommitteeView(generics.ListAPIView):
    """Credit Committee sees all applications awaiting committee decision."""
    serializer_class = ApprovalWorkflowSerializer
    permission_classes = [IsCreditCommittee]

    def get_queryset(self):
        return ApprovalWorkflow.objects.filter(
            status='PENDING_COMMITTEE'
        ).select_related('application', 'application__client')


class AllPendingView(generics.ListAPIView):
    """Admin/Manager sees full pending queue across all steps."""
    serializer_class = ApprovalWorkflowSerializer
    permission_classes = [IsBranchManager]

    def get_queryset(self):
        return ApprovalWorkflow.objects.exclude(
            status__in=['APPROVED', 'REJECTED']
        ).select_related('application')


# RISK ANALYST DECISION 

class RiskAnalystDecisionView(APIView):
    """
    Risk Analyst submits their review of the AI risk score and recommendation.
    Decision options: ESCALATE (to manager) or MORE_INFO (back to loan officer)
    """
    permission_classes = [IsRiskAnalyst]

    def post(self, request, loan_id):
        try:
            application = LoanApplication.objects.get(pk=loan_id)
        except LoanApplication.DoesNotExist:
            return Response({"error": "Application not found"}, status=404)

        workflow = _get_or_create_workflow(application)

        decision_value = request.data.get("decision")
        comments = request.data.get("comments", "")

        if not comments:
            return Response(
                {"error": "comments are required for all approval decisions."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if decision_value not in ["ESCALATE", "MORE_INFO"]:
            return Response(
                {"error": "Risk Analyst decision must be ESCALATE or MORE_INFO."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if analyst followed or overrode AI recommendation
        ai_followed = request.data.get("ai_recommendation_followed", None)
        override_reason = request.data.get("override_reason", "")
        if ai_followed is False and not override_reason:
            return Response(
                {"error": "override_reason required when not following AI recommendation."},
                status=status.HTTP_400_BAD_REQUEST
            )

        ApprovalDecision.objects.create(
            workflow=workflow,
            step='RISK_ANALYST',
            decision=decision_value,
            decided_by=request.user,
            comments=comments,
            ai_recommendation_followed=ai_followed,
            override_reason=override_reason,
        )
        
        # Log human decision
        ai_recommendation = getattr(
            getattr(application, 'risk_assessment', None),
            'recommendation_type', ''
        )
        log_human_decision(
            officer=request.user,
            decision_type='LOAN_APPROVAL',
            reference_model='LoanApplication',
            reference_id=application.id,
            decision=decision_value,
            reason=comments,
            ai_recommendation=ai_recommendation,
            followed_ai=ai_followed,
            override_justification=override_reason
        )
        
        # Log to main audit trail
        prev_status = application.status
        log_action(
            user=request.user,
            action_type='APPROVAL',
            model_name='LoanApplication',
            object_id=str(application.id),
            description=f"Risk Analyst decision: {decision_value} by {request.user.role}",
            request=request
        )

        if decision_value == "MORE_INFO":
            workflow.status = 'MORE_INFO_REQUIRED'
            workflow.save()
            log_status_change(
                application, application.status, 'MORE_INFO_REQUIRED',
                request.user, f"Risk Analyst: {comments}"
            )
        else:  # ESCALATE to manager
            workflow.status = 'PENDING_MANAGER_REVIEW'
            workflow.save()
            log_status_change(
                application, application.status, 'MANAGER_REVIEW',
                request.user, f"Risk Analyst escalated: {comments}"
            )

        return Response({
            "message": f"Risk Analyst decision recorded: {decision_value}",
            "workflow_status": workflow.status
        })


#  BRANCH MANAGER DECISION
class BranchManagerDecisionView(APIView):
    """
    Branch Manager can APPROVE (low risk), REJECT, MORE_INFO, or escalate to COMMITTEE.
    For HIGH risk or large loans, must escalate to committee.
    """
    permission_classes = [IsBranchManager]

    def post(self, request, loan_id):
        try:
            application = LoanApplication.objects.get(pk=loan_id)
            workflow = application.approval_workflow
        except (LoanApplication.DoesNotExist, ApprovalWorkflow.DoesNotExist):
            return Response({"error": "Not found"}, status=404)

        if workflow.status != 'PENDING_MANAGER_REVIEW':
            return Response(
                {"error": "Application is not pending manager review."},
                status=status.HTTP_400_BAD_REQUEST
            )

        decision_value = request.data.get("decision")
        comments = request.data.get("comments", "")

        if not comments:
            return Response(
                {"error": "comments are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if decision_value not in ["APPROVED", "REJECTED", "MORE_INFO", "ESCALATE"]:
            return Response(
                {"error": "Invalid decision. Choose: APPROVED, REJECTED, MORE_INFO, ESCALATE"},
                status=status.HTTP_400_BAD_REQUEST
            )

        ai_followed = request.data.get("ai_recommendation_followed", None)
        override_reason = request.data.get("override_reason", "")

        ApprovalDecision.objects.create(
            workflow=workflow,
            step='BRANCH_MANAGER',
            decision=decision_value,
            decided_by=request.user,
            comments=comments,
            ai_recommendation_followed=ai_followed,
            override_reason=override_reason,
        )
        
        # Log human decision
        ai_recommendation = getattr(
            getattr(application, 'risk_assessment', None),
            'recommendation_type', ''
        )
        log_human_decision(
            officer=request.user,
            decision_type='LOAN_APPROVAL',
            reference_model='LoanApplication',
            reference_id=application.id,
            decision=decision_value,
            reason=comments,
            ai_recommendation=ai_recommendation,
            followed_ai=ai_followed,
            override_justification=override_reason
        )
        
        # Log to main audit trail
        prev_status = application.status
        log_action(
            user=request.user,
            action_type='APPROVAL',
            model_name='LoanApplication',
            object_id=str(application.id),
            description=f"Manager decision: {decision_value} by {request.user.role}",
            status_before=prev_status,
            status_after=decision_value,
            request=request
        )

        if decision_value == "APPROVED":
            # Large loans MUST go to committee regardless
            if workflow.requires_committee:
                return Response(
                    {"error": (
                        f"Loans above LKR {COMMITTEE_THRESHOLD:,.0f} require Credit Committee approval. "
                        "Use ESCALATE decision."
                    )},
                    status=status.HTTP_400_BAD_REQUEST
                )
            workflow.status = 'APPROVED'
            workflow.save()
            log_status_change(application, application.status, 'APPROVED', request.user, comments)

        elif decision_value == "REJECTED":
            workflow.status = 'REJECTED'
            workflow.save()
            log_status_change(application, application.status, 'REJECTED', request.user, comments)

        elif decision_value == "MORE_INFO":
            workflow.status = 'MORE_INFO_REQUIRED'
            workflow.save()
            log_status_change(
                application, application.status, 'MORE_INFO_REQUIRED', request.user, comments
            )

        elif decision_value == "ESCALATE":
            workflow.status = 'PENDING_COMMITTEE'
            workflow.save()
            CommitteeDecision.objects.get_or_create(workflow=workflow)
            log_status_change(
                application, application.status, 'COMMITTEE_REVIEW', request.user, comments
            )

        return Response({
            "message": f"Branch Manager decision: {decision_value}",
            "workflow_status": workflow.status
        })


# CREDIT COMMITTEE DECISION 

class CommitteeVoteView(APIView):
    """
    Credit Committee members submit their vote.
    Requires minimum 2 votes to finalize.
    """
    permission_classes = [IsCreditCommittee]

    def post(self, request, loan_id):
        try:
            application = LoanApplication.objects.get(pk=loan_id)
            workflow = application.approval_workflow
            committee = workflow.committee_decision
        except Exception:
            return Response({"error": "Committee record not found."}, status=404)

        if workflow.status != 'PENDING_COMMITTEE':
            return Response(
                {"error": "Application is not pending committee review."},
                status=status.HTTP_400_BAD_REQUEST
            )

        vote = request.data.get("vote")   # "FOR" or "AGAINST"
        comments = request.data.get("comments", "")

        if vote not in ["FOR", "AGAINST"]:
            return Response(
                {"error": "vote must be FOR or AGAINST"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not comments:
            return Response({"error": "comments required"}, status=status.HTTP_400_BAD_REQUEST)

        # Record vote as ApprovalDecision
        ApprovalDecision.objects.create(
            workflow=workflow,
            step='CREDIT_COMMITTEE',
            decision="APPROVED" if vote == "FOR" else "REJECTED",
            decided_by=request.user,
            comments=comments,
        )

        if vote == "FOR":
            committee.vote_for += 1
        else:
            committee.vote_against += 1

        committee.save()

        # Quorum = 2 votes minimum; majority wins
        total_votes = committee.vote_for + committee.vote_against
        if total_votes >= 2:
            committee.quorum_reached = True
            if committee.vote_for > committee.vote_against:
                committee.final_decision = "APPROVED"
                workflow.status = "APPROVED"
                log_status_change(
                    application, application.status, 'APPROVED', request.user,
                    f"Committee approved ({committee.vote_for} for, {committee.vote_against} against)"
                )
            else:
                committee.final_decision = "REJECTED"
                workflow.status = "REJECTED"
                log_status_change(
                    application, application.status, 'REJECTED', request.user,
                    f"Committee rejected ({committee.vote_for} for, {committee.vote_against} against)"
                )
            committee.finalized_at = timezone.now()
            committee.save()
            workflow.save()

        return Response({
            "message": f"Vote recorded: {vote}",
            "votes_for": committee.vote_for,
            "votes_against": committee.vote_against,
            "quorum_reached": committee.quorum_reached,
            "final_decision": committee.final_decision or "Pending more votes"
        })


# APPROVAL HISTORY

class ApprovalHistoryView(APIView):
    permission_classes = [IsRiskAnalyst]

    def get(self, request, loan_id):
        try:
            workflow = ApprovalWorkflow.objects.get(application_id=loan_id)
        except ApprovalWorkflow.DoesNotExist:
            return Response({"error": "No workflow found"}, status=404)

        decisions = workflow.decisions.all()
        return Response({
            "application_number": workflow.application.application_number,
            "workflow_status": workflow.status,
            "requires_committee": workflow.requires_committee,
            "decisions": ApprovalDecisionSerializer(decisions, many=True).data
        })