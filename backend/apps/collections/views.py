from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django.utils import timezone
from decimal import Decimal

from .models import DelinquencyCase, CollectionAction, PromiseToPay, EscalationRecord
from .serializers import (
    DelinquencyCaseSerializer, CollectionActionSerializer,
    PromiseToPaySerializer, EscalationSerializer
)
from apps.loans.models import Loan
from apps.repayments.models import RepaymentInstallment
from apps.users.permissions import IsCollectionsOfficer, IsBranchManager
from apps.users.models import User


class CreateCasesFromA4View(APIView):
    """
    Called after A4 scan. Auto-creates or updates DelinquencyCase
    for each overdue loan returned by A4.
    """
    permission_classes = [IsCollectionsOfficer]

    def post(self, request):
        overdue_cases = request.data.get("overdue_cases", [])
        created = 0
        updated = 0

        for case_data in overdue_cases:
            try:
                loan = Loan.objects.get(pk=case_data["loan_id"])
            except Loan.DoesNotExist:
                continue

            # Calculate total overdue amount from overdue installments
            overdue_insts = RepaymentInstallment.objects.filter(
                schedule__loan=loan, status='OVERDUE'
            )
            total_overdue = sum(
                i.amount_due - i.amount_paid for i in overdue_insts
            )

            case, was_created = DelinquencyCase.objects.update_or_create(
                loan=loan,
                defaults={
                    "bucket": case_data.get("bucket", "BUCKET_1_7"),
                    "days_overdue": case_data.get("days_overdue", 0),
                    "total_overdue_amount": total_overdue,
                    "overdue_installments_count": overdue_insts.count(),
                    "status": "OPEN" if was_created else case.status,
                    "predicted_default_probability": case_data.get("predicted_default_probability"),
                    "behavioral_pattern_label": case_data.get("behavioral_pattern_label", ""),
                    "llm_recommended_action": case_data.get("llm_recommended_action", ""),
                }
            )
            if was_created:
                created += 1
            else:
                updated += 1

        return Response({
            "message": f"{created} case(s) created, {updated} updated.",
            "total_processed": len(overdue_cases)
        })


class OverdueCaseListView(generics.ListAPIView):
    """Collections Officer sees their assigned overdue cases."""
    serializer_class = DelinquencyCaseSerializer
    permission_classes = [IsCollectionsOfficer]

    def get_queryset(self):
        user = self.request.user
        qs = DelinquencyCase.objects.exclude(status__in=['RESOLVED', 'WRITTEN_OFF'])
        bucket = self.request.query_params.get('bucket')
        if bucket:
            qs = qs.filter(bucket=bucket)
        if user.role == 'collections_officer':
            return qs.filter(assigned_to=user)
        return qs  # Managers see all


class AssignCaseView(APIView):
    """Branch Manager assigns a delinquency case to a Collections Officer."""
    permission_classes = [IsBranchManager]

    def post(self, request, case_id):
        officer_id = request.data.get("officer_id")
        try:
            case = DelinquencyCase.objects.get(pk=case_id)
            officer = User.objects.get(pk=officer_id, role='collections_officer')
        except (DelinquencyCase.DoesNotExist, User.DoesNotExist):
            return Response({"error": "Case or officer not found."}, status=404)

        case.assigned_to = officer
        case.status = 'IN_PROGRESS'
        case.save()

        return Response({
            "message": f"Case assigned to {officer.get_full_name()}.",
            "case_id": case.id
        })


class LogContactAttemptView(APIView):
    """Collections Officer logs a contact attempt on a case."""
    permission_classes = [IsCollectionsOfficer]

    def post(self, request, case_id):
        try:
            case = DelinquencyCase.objects.get(pk=case_id)
        except DelinquencyCase.DoesNotExist:
            return Response({"error": "Case not found."}, status=404)

        serializer = CollectionActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        action = serializer.save(case=case, performed_by=request.user)

        # If outcome is promised payment, update case status
        if action.outcome == 'PROMISED_PAYMENT':
            case.status = 'PROMISE_TO_PAY'
            case.save()

        return Response({
            "message": "Contact attempt logged.",
            "action_id": action.id,
            "outcome": action.outcome
        }, status=status.HTTP_201_CREATED)


class RecordPromiseToPayView(APIView):
    """Records a formal Promise to Pay from the client."""
    permission_classes = [IsCollectionsOfficer]

    def post(self, request, case_id):
        try:
            case = DelinquencyCase.objects.get(pk=case_id)
        except DelinquencyCase.DoesNotExist:
            return Response({"error": "Case not found."}, status=404)

        serializer = PromiseToPaySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        ptp = serializer.save(case=case, recorded_by=request.user)
        case.status = 'PROMISE_TO_PAY'
        case.save()

        return Response({
            "message": "Promise to Pay recorded.",
            "promised_amount": str(ptp.promised_amount),
            "promised_date": str(ptp.promised_date),
        }, status=status.HTTP_201_CREATED)


class UpdatePromiseStatusView(APIView):
    """Mark a Promise to Pay as KEPT or BROKEN after the promised date."""
    permission_classes = [IsCollectionsOfficer]

    def post(self, request, ptp_id):
        try:
            ptp = PromiseToPay.objects.get(pk=ptp_id)
        except PromiseToPay.DoesNotExist:
            return Response({"error": "Promise not found."}, status=404)

        new_status = request.data.get("status")
        if new_status not in ['KEPT', 'BROKEN', 'EXTENDED']:
            return Response({"error": "Status must be KEPT, BROKEN, or EXTENDED."}, status=400)

        ptp.status = new_status
        ptp.outcome_notes = request.data.get("outcome_notes", "")
        if new_status == 'KEPT':
            ptp.fulfilled_at = timezone.now()
            ptp.case.status = 'RESOLVED'
            ptp.case.resolved_at = timezone.now()
            ptp.case.resolution_notes = "Promise to Pay fulfilled."
            ptp.case.save()
        ptp.save()

        return Response({"message": f"Promise marked as {new_status}."})


class EscalateCaseView(APIView):
    """Collections Officer escalates a 30+ day case to Branch Manager."""
    permission_classes = [IsCollectionsOfficer]

    def post(self, request, case_id):
        try:
            case = DelinquencyCase.objects.get(pk=case_id)
        except DelinquencyCase.DoesNotExist:
            return Response({"error": "Case not found."}, status=404)

        reason = request.data.get("reason")
        notes = request.data.get("notes", "")
        escalated_to_id = request.data.get("escalated_to_id")

        if not reason or not notes:
            return Response(
                {"error": "reason and notes are required for escalation."},
                status=400
            )

        try:
            escalated_to = User.objects.get(pk=escalated_to_id, role='branch_manager')
        except User.DoesNotExist:
            return Response({"error": "Escalation target must be a Branch Manager."}, status=400)

        EscalationRecord.objects.create(
            case=case,
            reason=reason,
            escalated_by=request.user,
            escalated_to=escalated_to,
            notes=notes
        )

        case.status = 'ESCALATED'
        case.bucket = 'BUCKET_OVER_30'
        case.save()

        return Response({
            "message": f"Case escalated to {escalated_to.get_full_name()}.",
            "case_status": case.status
        })


class CaseHistoryView(APIView):
    permission_classes = [IsCollectionsOfficer]

    def get(self, request, case_id):
        try:
            case = DelinquencyCase.objects.get(pk=case_id)
        except DelinquencyCase.DoesNotExist:
            return Response({"error": "Case not found."}, status=404)

        return Response(DelinquencyCaseSerializer(case).data)


class ResolveCaseView(APIView):
    """Manager or Collections Officer marks a case as resolved."""
    permission_classes = [IsCollectionsOfficer]

    def post(self, request, case_id):
        try:
            case = DelinquencyCase.objects.get(pk=case_id)
        except DelinquencyCase.DoesNotExist:
            return Response({"error": "Case not found."}, status=404)

        case.status = 'RESOLVED'
        case.resolved_at = timezone.now()
        case.resolution_notes = request.data.get("resolution_notes", "")
        case.save()

        return Response({"message": "Case resolved.", "case_id": case.id})