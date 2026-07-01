from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
import httpx
import json
from django.conf import settings

from .models import Client, ClientAddress, ClientBusiness, ClientIncome
from apps.audit.utils import log_agent_action
from apps.kyc.models import KYCDocument, KYCChecklist
from .serializers import (
    ClientListSerializer, ClientDetailSerializer,
    CreateClientSerializer, ClientAddressSerializer,
    ClientBusinessSerializer, ClientIncomeSerializer,
    KYCDocumentSerializer, KYCChecklistSerializer
)
from apps.users.permissions import IsLoanOfficer, IsAdmin


class ClientListCreateView(generics.ListCreateAPIView):
    queryset = Client.objects.all().order_by('-created_at')
    permission_classes = [IsLoanOfficer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['first_name', 'last_name', 'nic_number', 'phone_primary']
    ordering_fields = ['created_at', 'data_quality_score']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateClientSerializer
        return ClientListSerializer

    def perform_create(self, serializer):
        client = serializer.save(registered_by=self.request.user)
        # Auto-create KYC checklist when client is created
        KYCChecklist.objects.create(client=client)


class ClientDetailView(generics.RetrieveUpdateAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientDetailSerializer
    permission_classes = [IsLoanOfficer]


class ClientAddressView(generics.CreateAPIView):
    serializer_class = ClientAddressSerializer
    permission_classes = [IsLoanOfficer]

    def perform_create(self, serializer):
        client = Client.objects.get(pk=self.kwargs['client_id'])
        serializer.save(client=client)


class ClientBusinessView(generics.CreateAPIView):
    serializer_class = ClientBusinessSerializer
    permission_classes = [IsLoanOfficer]

    def perform_create(self, serializer):
        client = Client.objects.get(pk=self.kwargs['client_id'])
        # Use get_or_create to prevent duplicate OneToOne relation
        business, created = ClientBusiness.objects.get_or_create(
            client=client,
            defaults={field: serializer.validated_data.get(field) for field in serializer.validated_data}
        )
        if not created:
            # Update existing record
            for field, value in serializer.validated_data.items():
                setattr(business, field, value)
            business.save()


class ClientIncomeView(generics.CreateAPIView):
    serializer_class = ClientIncomeSerializer
    permission_classes = [IsLoanOfficer]

    def perform_create(self, serializer):
        client = Client.objects.get(pk=self.kwargs['client_id'])
        # Use get_or_create to prevent duplicate OneToOne relation
        income, created = ClientIncome.objects.get_or_create(
            client=client,
            defaults={field: serializer.validated_data.get(field) for field in serializer.validated_data}
        )
        if not created:
            # Update existing record
            for field, value in serializer.validated_data.items():
                setattr(income, field, value)
            income.save()


class DocumentUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsLoanOfficer]

    def post(self, request, client_id):
        client = Client.objects.get(pk=client_id)
        file = request.FILES.get('file')
        doc_type = request.data.get('document_type')

        if not file or not doc_type:
            return Response(
                {"error": "file and document_type are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        doc = KYCDocument.objects.create(
            client=client,
            document_type=doc_type,
            file=file,
            file_name=file.name,
            uploaded_by=request.user
        )
        return Response(KYCDocumentSerializer(doc).data, status=status.HTTP_201_CREATED)


class KYCChecklistUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = KYCChecklistSerializer
    permission_classes = [IsLoanOfficer]

    def get_object(self):
        return KYCChecklist.objects.get(client_id=self.kwargs['client_id'])


class A1ValidateClientView(APIView):
    """Trigger A1 agent to validate client data quality."""
    permission_classes = [IsLoanOfficer]

    def post(self, request, client_id):
        client = Client.objects.get(pk=client_id)
        checklist = client.kyc_checklist

        # Build input payload for A1
        payload = {
            "client_id": client.id,
            "client_data": {
                "nic_number": client.nic_number,
                "first_name": client.first_name,
                "last_name": client.last_name,
                "date_of_birth": str(client.date_of_birth),
                "gender": client.gender,
                "phone_primary": client.phone_primary,
                "addresses": list(client.addresses.values()),
                "income": {
                    "monthly_income": str(client.income.monthly_income)
                } if hasattr(client, 'income') else {}
            },
            "kyc_data": {
                "nic_verified": checklist.nic_verified,
                "address_verified": checklist.address_verified,
                "income_verified": checklist.income_verified,
                "aml_check_done": checklist.aml_check_done,
            }
        }

        # Call A1 via FastAPI
        try:
            response = httpx.post(
                f"{settings.AI_SERVICE_URL}/api/a1/validate-client",
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

        # Save quality score back to client
        output = ai_result.get("output") or {}
        if output:
            client.data_quality_score = output.get("data_quality_score")
            client.data_quality_notes = ai_result.get("rationale", "")

        usage_metadata = output.get("usage_metadata", {})
        log_agent_action(
            agent_id="A1",
            agent_name="Data Collection Agent",
            input_reference=f"client:{client.id}",
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

        # Update status to KYC_SUBMITTED
        client.status = 'KYC_SUBMITTED'
        client.save()

        return Response(ai_result)