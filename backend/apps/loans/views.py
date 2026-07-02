# Standard Library
from decimal import Decimal
import json
import logging

# Third-Party
import httpx
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import filters

logger = logging.getLogger(__name__)

# Local Apps
from apps.audit.utils import log_agent_action
from apps.users.permissions import (
    IsAdmin, IsBranchManager, IsFinanceStaff, IsLoanOfficer, IsRiskAnalyst
)

# Local Models
from .models import (
    AIRecommendation, CashflowAssessment, CreditMemo, Disbursement,
    DisbursementCondition, Loan, LoanApplication, LoanDocument, LoanProduct,
    OfficerFeedback, RiskAssessment, RiskScoreHistory
)

# Local Serializers
from .serializers import (
    AIRecommendationSerializer, CashflowSerializer,
    CreateLoanApplicationSerializer, CreditMemoSerializer,
    LoanApplicationDetailSerializer, LoanApplicationListSerializer,
    LoanDocumentSerializer, LoanProductSerializer,
    RiskAssessmentSerializer
)

# Local Utilities
from .repayment_utils import calculate_monthly_installment, generate_repayment_schedule
from .utils import log_status_change


class LoanProductListView(generics.ListAPIView):
    queryset = LoanProduct.objects.filter(is_active=True)
    serializer_class = LoanProductSerializer


class LoanApplicationListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsLoanOfficer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['application_number', 'client__first_name', 'client__last_name', 'client__nic_number']

    def get_queryset(self):
        user = self.request.user
        # Loan officers see their own applications; admins/managers see all
        if user.role in ['admin', 'branch_manager', 'risk_analyst', 'credit_committee', 'finance_staff', 'collections_officer', 'compliance_officer']:
            return LoanApplication.objects.all()
        return LoanApplication.objects.filter(created_by=user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateLoanApplicationSerializer
        return LoanApplicationListSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        # Calculate status counts on the full filtered queryset
        from django.db.models import Count
        status_counts_qs = queryset.values('status').annotate(count=Count('status'))
        status_counts = {item['status']: item['count'] for item in status_counts_qs}
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data['status_counts'] = status_counts
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'status_counts': status_counts,
            'results': serializer.data
        })

    def perform_create(self, serializer):
        application = serializer.save(created_by=self.request.user, status='DRAFT')
        log_status_change(
            application=application,
            from_status='',
            to_status='DRAFT',
            user=self.request.user,
            reason="Application created"
        )


class LoanApplicationDetailView(generics.RetrieveUpdateAPIView):
    queryset = LoanApplication.objects.all()
    permission_classes = [IsLoanOfficer]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CreateLoanApplicationSerializer
        return LoanApplicationDetailSerializer

    def update(self, request, *args, **kwargs):
        application = self.get_object()
        if application.status not in ['DRAFT', 'MORE_INFO_REQUIRED']:
            return Response(
                {"error": "Only DRAFT or MORE_INFO_REQUIRED applications can be edited."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)


class SubmitApplicationView(APIView):
    """
    Loan officer submits a DRAFT application.
    Status moves: DRAFT → SUBMITTED → AI_SCREENING
    """
    permission_classes = [IsLoanOfficer]

    def post(self, request, pk):
        try:
            application = LoanApplication.objects.get(pk=pk)
        except LoanApplication.DoesNotExist:
            return Response({"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND)

        if application.status not in ['DRAFT', 'MORE_INFO_REQUIRED']:
            return Response(
                {"error": f"Cannot submit an application with status '{application.status}'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not hasattr(application, 'cashflow'):
            return Response(
                {"error": "Cashflow assessment is required before submission."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # SUBMITTED - set submitted_at before logging status change
        application.submitted_at = timezone.now()
        application.save()
        
        log_status_change(
            application=application,
            from_status=application.status,
            to_status='SUBMITTED',
            user=request.user,
            reason="Application submitted by loan officer"
        )

        return Response({
            "message": "Application submitted successfully. Pending KYC validation.",
            "application_number": application.application_number,
            "status": application.status
        })


class ApplicationStatusView(APIView):
    """Returns the current status and full history of an application."""
    permission_classes = [IsLoanOfficer]

    def get(self, request, pk):
        try:
            application = LoanApplication.objects.get(pk=pk)
        except LoanApplication.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        history = application.status_history.all()
        return Response({
            "application_number": application.application_number,
            "current_status": application.status,
            "status_display": application.get_status_display(),
            "history": [
                {
                    "from": h.from_status,
                    "to": h.to_status,
                    "by": h.changed_by.get_full_name() if h.changed_by else "System",
                    "role": h.changed_by_role,
                    "reason": h.reason,
                    "at": h.timestamp
                }
                for h in history
            ]
        })


class CashflowCreateView(generics.CreateAPIView):
    serializer_class = CashflowSerializer
    permission_classes = [IsLoanOfficer]

    def perform_create(self, serializer):
        try:
            application = LoanApplication.objects.get(pk=self.kwargs['pk'])
        except LoanApplication.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Application not found.")
        # Use update_or_create to handle duplicate OneToOne field gracefully
        cashflow, created = CashflowAssessment.objects.update_or_create(
            application=application,
            defaults=serializer.validated_data
        )
        cashflow.calculate_ratios()
        cashflow.save()


class LoanDocumentUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsLoanOfficer]

    def post(self, request, pk):
        try:
            application = LoanApplication.objects.get(pk=pk)
        except LoanApplication.DoesNotExist:
            return Response(
                {"error": "Application not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        file = request.FILES.get('file')
        doc_type = request.data.get('document_type')

        if not file or not doc_type:
            return Response(
                {"error": "file and document_type are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        doc = LoanDocument.objects.create(
            application=application,
            document_type=doc_type,
            file=file,
            file_name=file.name,
            uploaded_by=request.user,
            notes=request.data.get('notes', '')
        )
        return Response(LoanDocumentSerializer(doc).data, status=status.HTTP_201_CREATED)
class TriggerRiskAssessmentView(APIView):
    """
    Called after application enters AI_SCREENING.
    Builds payload, calls A2, saves result to DB.
    """
    permission_classes = [IsRiskAnalyst]

    def post(self, request, pk):
        try:
            application = LoanApplication.objects.get(pk=pk)
        except LoanApplication.DoesNotExist:
            return Response({"error": "Application not found"}, status=404)

        if application.status != 'AI_SCREENING':
            return Response(
                {"error": "Application must be in AI_SCREENING status to run risk assessment."},
                status=status.HTTP_400_BAD_REQUEST
            )

        client = application.client
        income = getattr(client, 'income', None)
        cashflow = getattr(application, 'cashflow', None)
        business = getattr(client, 'business', None)

        # Build A2 payload
        payload = {
            "loan_id": application.id,
            "client_data": {
                "monthly_income": str(income.monthly_income) if income else "0",
                "number_of_dependents": income.number_of_dependents if income else 0,
                "data_quality_score": client.data_quality_score or 0,
                "years_in_operation": business.years_in_operation if business else 0,
            },
            "loan_data": {
                "requested_amount": str(application.requested_amount),
                "requested_duration_months": application.requested_duration_months,
                "debt_to_income_ratio": cashflow.debt_to_income_ratio if cashflow else None,
            },
            "repayment_history": {
                "previous_loans_count": 0,   # Will come from repayment module in later phases
                "missed_payments": 0,
            }
        }

        # Call A2
        try:
            response = httpx.post(
                f"{settings.AI_SERVICE_URL}/api/a2/risk-score",
                json=payload,
                headers={"x-api-key": settings.AI_SERVICE_API_KEY},
                timeout=120.0
            )
            ai_result = response.json()
        except Exception as e:
            return Response(
                {"error": f"AI service unavailable: {str(e)}. Manual review required."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        output = ai_result.get("output") or {}
        factor_scores = output.get("factor_scores") or {}

        usage_metadata = ai_result.get("usage_metadata") or {}
        log_agent_action(
            agent_id="A2",
            agent_name="Risk Assessment Agent",
            input_reference=f"loan:{application.id}",
            input_payload=payload,
            output_payload=output,
            confidence=ai_result.get("confidence", 0),
            rationale=ai_result.get("rationale", ""),
            triggered_by=request.user,
            response_time_ms=None,
            trigger_type="manual",
            llm_model_used=usage_metadata.get("model_used", ""),
            prompt_tokens_used=usage_metadata.get("prompt_tokens", 0),
            completion_tokens_used=usage_metadata.get("completion_tokens", 0),
            llm_raw_response=json.dumps(ai_result, default=str),
            hallucination_check_passed=True
        )

        # Save RiskAssessment to DB
        RiskAssessment.objects.update_or_create(
            application=application,
            defaults={
                "risk_score": output.get("risk_score", 0),
                "risk_category": output.get("risk_category", "HIGH"),
                "confidence": ai_result.get("confidence", 0),
                "ai_rationale": ai_result.get("rationale", ""),
                "dti_score": factor_scores.get("dti_score", 0),
                "lti_score": factor_scores.get("lti_score", 0),
                "kyc_score": factor_scores.get("kyc_score", 0),
                "income_stability_score": factor_scores.get("income_stability_score", 0),
                "repayment_history_score": factor_scores.get("repayment_history_score", 0),
                "dependents_score": factor_scores.get("dependents_score", 0),
                "default_signals": output.get("default_signals", []),
            }
        )

        # Save to risk history
        RiskScoreHistory.objects.create(
            client=client,
            application=application,
            risk_score=output.get("risk_score", 0),
            risk_category=output.get("risk_category", "HIGH"),
        )

        # Auto-generate credit memo
        memo_content = self._build_credit_memo(application, ai_result)
        CreditMemo.objects.update_or_create(
            application=application,
            defaults={"content": memo_content}
        )

        return Response({
            "message": "Risk assessment completed.",
            "risk_score": output.get("risk_score"),
            "risk_category": output.get("risk_category"),
            "agent_response": ai_result
        })

    def _build_credit_memo(self, application, ai_result):
        output = ai_result.get("output") or {}
        signals = output.get("default_signals", [])
        return f"""
CREDIT MEMO
===========
Application No : {application.application_number}
Client         : {application.client.first_name} {application.client.last_name}
NIC            : {application.client.nic_number}
Loan Amount    : LKR {application.requested_amount}
Duration       : {application.requested_duration_months} months
Purpose        : {application.get_loan_purpose_display()}

AI RISK ASSESSMENT (A2)
-----------------------
Risk Score     : {output.get('risk_score')} / 100
Risk Category  : {output.get('risk_category')}
Confidence     : {round(ai_result.get('confidence', 0) * 100, 1)}%
Rationale      : {ai_result.get('rationale')}

DEFAULT SIGNALS
---------------
{chr(10).join(f'- {s}' for s in signals) if signals else '- No signals detected'}

REQUIRED ACTION
---------------
{output.get('required_action')}

NOTE: This memo is generated by AI Agent A2.
      All final decisions must be made by authorized human staff.
        """


class RiskAnalystReviewView(APIView):
    """Risk analyst reviews A2 output and adds their notes."""
    permission_classes = [IsRiskAnalyst]

    def post(self, request, pk):
        try:
            application = LoanApplication.objects.get(pk=pk)
            risk = application.risk_assessment
        except (LoanApplication.DoesNotExist, RiskAssessment.DoesNotExist):
            return Response({"error": "Not found"}, status=404)

        analyst_notes = request.data.get("analyst_notes", "")
        if not analyst_notes:
            return Response(
                {"error": "analyst_notes is required for review."},
                status=status.HTTP_400_BAD_REQUEST
            )

        risk.reviewed_by = request.user
        risk.reviewed_at = timezone.now()
        risk.analyst_notes = analyst_notes
        risk.save()

        # Advance status
        from .utils import log_status_change
        log_status_change(
            application=application,
            from_status=application.status,
            to_status='RISK_REVIEWED',
            user=request.user,
            reason=f"Risk Analyst reviewed. Notes: {analyst_notes}"
        )

        return Response({
            "message": "Risk review completed.",
            "application_number": application.application_number,
            "status": application.status
        })


class RiskHistoryView(generics.ListAPIView):
    permission_classes = [IsRiskAnalyst]

    def get(self, request, client_id):
        history = RiskScoreHistory.objects.filter(client_id=client_id)
        data = [
            {
                "application_number": h.application.application_number,
                "risk_score": h.risk_score,
                "risk_category": h.risk_category,
                "scored_at": h.scored_at
            }
            for h in history
        ]
        return Response(data)
    

class TriggerRecommendationView(APIView):
    """
    Calls A3 after A2 risk assessment is complete.
    Should be triggered right after TriggerRiskAssessmentView.
    """
    permission_classes = [IsRiskAnalyst]

    def post(self, request, pk):
        try:
            application = LoanApplication.objects.get(pk=pk)
            risk = application.risk_assessment
        except (LoanApplication.DoesNotExist, RiskAssessment.DoesNotExist):
            return Response(
                {"error": "Risk assessment not found. Run A2 first."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # BUG-BE-16: Check application status before calling A3
        if application.status not in ['AI_SCREENING', 'RISK_ASSESSED']:
            return Response(
                {"error": f"Application must be in AI_SCREENING or RISK_ASSESSED status, currently: {application.status}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        client = application.client
        income = getattr(client, 'income', None)
        cashflow = getattr(application, 'cashflow', None)

        payload = {
            "loan_id": application.id,
            "risk_score": risk.risk_score,
            "risk_category": risk.risk_category,
            "default_signals": risk.default_signals,
            "kyc_score": client.data_quality_score or 0,
            "requested_amount": float(application.requested_amount),
            "monthly_income": float(income.monthly_income) if income else 0,
            "requested_duration_months": application.requested_duration_months,
            "debt_to_income_ratio": cashflow.debt_to_income_ratio if cashflow else 0,
            "has_repayment_history": False,  # Updated in Phase 9
        }

        try:
            response = httpx.post(
                f"{settings.AI_SERVICE_URL}/api/a3/recommendation",
                json=payload,
                headers={"x-api-key": settings.AI_SERVICE_API_KEY},
                timeout=120.0
            )
            ai_result = response.json()
        except Exception as e:
            return Response(
                {"error": f"AI service unavailable: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        output = ai_result.get("output") or {}
        usage_metadata = output.get("usage_metadata") or {}

        # Guard: if AI returned null output (LLM failure/low confidence), bail early
        if not output or not output.get("recommendation_type"):
            log_agent_action(
                agent_id="A3",
                agent_name="Recommendation Agent",
                input_reference=f"loan:{application.id}",
                input_payload=payload,
                output_payload=output,
                confidence=ai_result.get("confidence", 0),
                rationale=ai_result.get("rationale", "Low confidence or LLM failure."),
                triggered_by=request.user,
                response_time_ms=None,
                trigger_type="manual",
                llm_model_used=usage_metadata.get("model_used", ""),
                prompt_tokens_used=usage_metadata.get("prompt_tokens", 0),
                completion_tokens_used=usage_metadata.get("completion_tokens", 0),
                llm_raw_response=json.dumps(ai_result, default=str),
                hallucination_check_passed=False
            )
            return Response(
                {
                    "error": "AI Recommendation could not be generated (low confidence or LLM failure).",
                    "reason": ai_result.get("rationale", "Low confidence or LLM failure."),
                    "ai_status": ai_result.get("status", "UNKNOWN"),
                    "agent_response": ai_result
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        log_agent_action(
            agent_id="A3",
            agent_name="Recommendation Agent",
            input_reference=f"loan:{application.id}",
            input_payload=payload,
            output_payload=output,
            confidence=ai_result.get("confidence", 0),
            rationale=ai_result.get("rationale", ""),
            triggered_by=request.user,
            response_time_ms=None,
            trigger_type="manual",
            llm_model_used=usage_metadata.get("model_used", ""),
            prompt_tokens_used=usage_metadata.get("prompt_tokens", 0),
            completion_tokens_used=usage_metadata.get("completion_tokens", 0),
            llm_raw_response=json.dumps(ai_result, default=str),
            hallucination_check_passed=True
        )

        AIRecommendation.objects.update_or_create(
            application=application,
            defaults={
                "recommendation_type": output.get("recommendation_type"),
                "recommended_amount": output.get("recommended_amount"),
                "recommended_duration_months": output.get("recommended_duration_months"),
                "explanation": output.get("explanation", ""),
                "reasons": output.get("reasons", []),
                "confidence": ai_result.get("confidence", 0),
                "officer_decision": "PENDING",
            }
        )

        return Response({
            "message": "Recommendation generated.",
            "recommendation": output.get("recommendation_type"),
            "explanation": output.get("explanation"),
            "agent_response": ai_result
        })


class GetRecommendationView(generics.RetrieveAPIView):
    serializer_class = AIRecommendationSerializer
    permission_classes = [IsRiskAnalyst]

    def get_object(self):
        return AIRecommendation.objects.get(application_id=self.kwargs['pk'])


class OfficerFeedbackView(APIView):
    """
    Officer submits feedback on whether the AI recommendation was helpful.
    Also used to accept or override the recommendation.
    """
    permission_classes = [IsRiskAnalyst]

    def post(self, request, pk):
        try:
            rec = AIRecommendation.objects.get(application_id=pk)
        except AIRecommendation.DoesNotExist:
            return Response({"error": "Recommendation not found"}, status=404)

        decision = request.data.get("officer_decision")  # ACCEPTED or OVERRIDDEN
        override_reason = request.data.get("override_reason", "")

        if decision not in ["ACCEPTED", "OVERRIDDEN"]:
            return Response(
                {"error": "officer_decision must be ACCEPTED or OVERRIDDEN"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if decision == "OVERRIDDEN" and not override_reason:
            return Response(
                {"error": "override_reason is required when overriding an AI recommendation."},
                status=status.HTTP_400_BAD_REQUEST
            )

        rec.officer_decision = decision
        rec.officer_override_reason = override_reason
        rec.reviewed_by = request.user
        rec.reviewed_at = timezone.now()
        rec.save()

        # Save feedback
        OfficerFeedback.objects.create(
            recommendation=rec,
            officer=request.user,
            was_helpful=request.data.get("was_helpful", True),
            comment=request.data.get("comment", "")
        )

        return Response({
            "message": f"Recommendation {decision.lower()} by {request.user.get_full_name()}.",
            "application_number": rec.application.application_number
        })



class ReadyForDisbursementView(generics.ListAPIView):
    """Finance Staff sees loans that are APPROVED and ready to disburse."""
    permission_classes = [IsFinanceStaff]

    def get(self, request):
        applications = LoanApplication.objects.filter(status='APPROVED').select_related(
            'client', 'approval_workflow'
        )
        data = [
            {
                "id": app.id,
                "application_number": app.application_number,
                "client": f"{app.client.first_name} {app.client.last_name}",
                "requested_amount": app.requested_amount,
                "approved_at": app.updated_at,
            }
            for app in applications
        ]
        return Response(data)


class VerifyDisbursementConditionsView(APIView):
    """Finance Staff verifies pre-disbursement checklist items."""
    permission_classes = [IsFinanceStaff]

    def get(self, request, pk):
        conditions = DisbursementCondition.objects.filter(application_id=pk)
        return Response([
            {
                "id": c.id,
                "condition": c.condition_text,
                "is_met": c.is_met,
                "notes": c.notes
            }
            for c in conditions
        ])

    def post(self, request, pk):
        """Mark a condition as met."""
        condition_id = request.data.get("condition_id")
        try:
            condition = DisbursementCondition.objects.get(id=condition_id, application_id=pk)
        except DisbursementCondition.DoesNotExist:
            return Response({"error": "Condition not found"}, status=404)

        condition.is_met = True
        condition.verified_by = request.user
        condition.verified_at = timezone.now()
        condition.notes = request.data.get("notes", "")
        condition.save()

        return Response({"message": "Condition verified", "condition": condition.condition_text})


class ProcessDisbursementView(APIView):
    """
    Finance Staff processes the disbursement.
    Requires: all conditions met, manager authorization.
    Creates Loan record and generates repayment schedule.
    Wrapped in transaction.atomic to ensure atomicity.
    """
    permission_classes = [IsFinanceStaff]

    @transaction.atomic
    def post(self, request, pk):
        try:
            application = LoanApplication.objects.get(pk=pk)
        except LoanApplication.DoesNotExist:
            return Response({"error": "Application not found"}, status=404)

        if application.status != 'APPROVED':
            return Response(
                {"error": "Only APPROVED applications can be disbursed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check all conditions are met
        unmet = DisbursementCondition.objects.filter(application=application, is_met=False)
        if unmet.exists():
            return Response(
                {
                    "error": "Not all disbursement conditions have been met.",
                    "unmet_conditions": [c.condition_text for c in unmet]
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate required fields
        method = request.data.get("disbursement_method", "CASH")
        authorized_by_id = request.data.get("authorized_by_id")

        if not authorized_by_id:
            # Infer from ApprovalDecision
            from apps.approvals.models import ApprovalDecision
            manager_decision = ApprovalDecision.objects.filter(
                workflow__application=application,
                step='BRANCH_MANAGER',
                decision='APPROVED'
            ).order_by('-decided_at').first()
            
            if manager_decision and manager_decision.decided_by:
                authorized_by_id = manager_decision.decided_by.id

        if not authorized_by_id:
            return Response(
                {"error": "authorized_by_id (Branch Manager user ID) is required and could not be inferred."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify authorizer is a branch manager
        from apps.users.models import User
        try:
            authorizer = User.objects.get(pk=authorized_by_id, role='branch_manager')
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid authorizer. Must be a Branch Manager."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get interest rate from loan product or default
        interest_rate = Decimal('18.0')
        if application.loan_product:
            interest_rate = application.loan_product.interest_rate

        # Calculate installment
        monthly_installment, total_repayable = calculate_monthly_installment(
            principal=application.requested_amount,
            annual_rate=interest_rate,
            months=application.requested_duration_months
        )

        now = timezone.now()
        closure_date = now.date() + relativedelta(months=application.requested_duration_months)

        # Create Loan record
        loan = Loan.objects.create(
            application=application,
            client=application.client,
            principal_amount=application.requested_amount,
            interest_rate=interest_rate,
            duration_months=application.requested_duration_months,
            monthly_installment=monthly_installment,
            total_repayable=total_repayable,
            outstanding_balance=total_repayable,
            status='ACTIVE',
            disbursed_at=now,
            expected_closure_date=closure_date
        )

        # Create Disbursement record
        disbursement = Disbursement.objects.create(
            application=application,
            loan=loan,
            amount=application.requested_amount,
            method=method,
            reference_number=request.data.get("reference_number", ""),
            bank_name=request.data.get("bank_name", ""),
            account_number=request.data.get("account_number", ""),
            authorized_by=authorizer,
            processed_by=request.user,
            notes=request.data.get("notes", "")
        )

        # Advance application status
        log_status_change(
            application=application,
            from_status=application.status,
            to_status='DISBURSED',
            user=request.user,
            reason=f"Disbursed LKR {application.requested_amount} via {method}"
        )

        # Generate repayment schedule
        schedule_created = True
        schedule_error = None
        try:
            schedule = generate_repayment_schedule(loan)
        except Exception as e:
            schedule_created = False
            schedule_error = str(e)
            logger.error(f"Failed to generate repayment schedule for loan {loan.id}: {schedule_error}")
            # Re-raise to trigger transaction rollback on critical error
            raise

        return Response({
            "message": "Loan disbursed successfully.",
            "loan_number": loan.loan_number,
            "disbursement_amount": str(loan.principal_amount),
            "monthly_installment": str(monthly_installment),
            "total_repayable": str(total_repayable),
            "first_due_date": str(now.date() + relativedelta(months=1)),
            "expected_closure": str(closure_date),
            "repayment_schedule_created": schedule_created
        })


class DisbursementReceiptView(APIView):
    """Returns the disbursement receipt for a loan."""
    permission_classes = [IsFinanceStaff]

    def get(self, request, pk):
        try:
            disbursement = Disbursement.objects.get(application_id=pk)
            loan = disbursement.loan
        except Disbursement.DoesNotExist:
            return Response({"error": "Disbursement not found"}, status=404)

        return Response({
            "receipt": {
                "loan_number": loan.loan_number,
                "application_number": disbursement.application.application_number,
                "client_name": f"{loan.client.first_name} {loan.client.last_name}",
                "client_nic": loan.client.nic_number,
                "disbursement_method": disbursement.method,
                "reference_number": disbursement.reference_number,
                "principal_amount": str(loan.principal_amount),
                "interest_rate": f"{loan.interest_rate}% p.a.",
                "duration": f"{loan.duration_months} months",
                "monthly_installment": str(loan.monthly_installment),
                "total_repayable": str(loan.total_repayable),
                "disbursed_at": disbursement.disbursed_at,
                "expected_closure": loan.expected_closure_date,
                "authorized_by": disbursement.authorized_by.get_full_name(),
                "processed_by": disbursement.processed_by.get_full_name(),
            }
        })