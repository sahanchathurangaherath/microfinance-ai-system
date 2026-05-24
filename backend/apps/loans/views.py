from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone

from .models import LoanApplication, CashflowAssessment, LoanDocument, LoanProduct
from .serializers import (
    LoanApplicationListSerializer, LoanApplicationDetailSerializer,
    CreateLoanApplicationSerializer, CashflowSerializer,
    LoanDocumentSerializer, LoanProductSerializer
)
from .utils import log_status_change
from apps.users.permissions import IsLoanOfficer, IsAdmin


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