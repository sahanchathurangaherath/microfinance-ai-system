from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from django.conf import settings
import httpx
from .models import RiskAssessment, RiskScoreHistory, CreditMemo
from .serializers import RiskAssessmentSerializer, CreditMemoSerializer

from .models import LoanApplication, CashflowAssessment, LoanDocument, LoanProduct
from .serializers import (
    LoanApplicationListSerializer, LoanApplicationDetailSerializer,
    CreateLoanApplicationSerializer, CashflowSerializer,
    LoanDocumentSerializer, LoanProductSerializer
)
from .utils import log_status_change
from apps.users.permissions import IsLoanOfficer, IsAdmin, IsRiskAnalyst


class LoanProductListView(generics.ListAPIView):
    queryset = LoanProduct.objects.filter(is_active=True)
    serializer_class = LoanProductSerializer


class LoanApplicationListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsLoanOfficer]

    def get_queryset(self):
        user = self.request.user
        # Loan officers see their own applications; admins/managers see all
        if user.role in ['admin', 'branch_manager', 'risk_analyst', 'credit_committee']:
            return LoanApplication.objects.all()
        return LoanApplication.objects.filter(created_by=user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateLoanApplicationSerializer
        return LoanApplicationListSerializer

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

        # SUBMITTED
        log_status_change(
            application=application,
            from_status=application.status,
            to_status='SUBMITTED',
            user=request.user,
            reason="Application submitted by loan officer"
        )
        application.submitted_at = timezone.now()
        application.save()

        # Move to AI_SCREENING immediately
        log_status_change(
            application=application,
            from_status='SUBMITTED',
            to_status='AI_SCREENING',
            user=request.user,
            reason="Entered AI screening queue"
        )

        return Response({
            "message": "Application submitted successfully. Now in AI screening queue.",
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
        application = LoanApplication.objects.get(pk=self.kwargs['pk'])
        cashflow = serializer.save(application=application)
        cashflow.calculate_ratios()
        cashflow.save()


class LoanDocumentUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsLoanOfficer]

    def post(self, request, pk):
        application = LoanApplication.objects.get(pk=pk)
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
    permission_classes = [IsLoanOfficer]

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
                timeout=15.0
            )
            ai_result = response.json()
        except Exception as e:
            return Response(
                {"error": f"AI service unavailable: {str(e)}. Manual review required."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        output = ai_result.get("output", {})
        factor_scores = output.get("factor_scores", {})

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
        output = ai_result.get("output", {})
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