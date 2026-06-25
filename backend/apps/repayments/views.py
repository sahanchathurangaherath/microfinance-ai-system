from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import httpx
from django.conf import settings
from datetime import date

from .models import (
    RepaymentSchedule, RepaymentInstallment,
    Payment, PaymentReceipt
)
from apps.loans.models import Loan
from apps.users.permissions import IsFinanceStaff, IsCollectionsOfficer, IsLoanOfficer


class RepaymentScheduleView(APIView):
    permission_classes = [IsLoanOfficer]

    def get(self, request, loan_id):
        try:
            loan = Loan.objects.get(pk=loan_id)
            schedule = loan.schedule
        except (Loan.DoesNotExist, RepaymentSchedule.DoesNotExist):
            return Response({"error": "Schedule not found"}, status=404)

        installments = schedule.installments.all()
        return Response({
            "loan_number": loan.loan_number,
            "client": f"{loan.client.first_name} {loan.client.last_name}",
            "principal": str(loan.principal_amount),
            "interest_rate": str(loan.interest_rate),
            "duration_months": loan.duration_months,
            "monthly_installment": str(loan.monthly_installment),
            "total_repayable": str(loan.total_repayable),
            "outstanding_balance": str(loan.outstanding_balance),
            "disbursed_at": loan.disbursed_at,
            "expected_closure": loan.expected_closure_date,
            "installments": [
                {
                    "id": i.id,
                    "number": i.installment_number,
                    "due_date": i.due_date,
                    "amount_due": str(i.amount_due),
                    "amount_paid": str(i.amount_paid),
                    "outstanding": str(i.amount_due - i.amount_paid),
                    "status": i.status,
                    "days_overdue": i.days_overdue,
                    "penalty": str(i.penalty_amount),
                }
                for i in installments
            ]
        })


class PostPaymentView(APIView):
    """Finance Staff posts a payment against a specific installment.
    Wrapped in transaction.atomic to ensure atomicity across:
    - Payment creation
    - Installment status update
    - Loan balance update
    - Receipt generation
    """
    permission_classes = [IsFinanceStaff]

    @transaction.atomic
    def post(self, request):
        loan_id = request.data.get("loan_id")
        installment_id = request.data.get("installment_id")
        amount = Decimal(str(request.data.get("amount", 0)))
        method = request.data.get("method", "CASH")
        payment_date = request.data.get("payment_date", str(date.today()))
        reference = request.data.get("reference_number", "")

        if amount <= 0:
            return Response({"error": "Payment amount must be greater than 0."}, status=400)

        try:
            loan = Loan.objects.get(pk=loan_id)
            installment = RepaymentInstallment.objects.get(pk=installment_id)
        except (Loan.DoesNotExist, RepaymentInstallment.DoesNotExist):
            return Response({"error": "Loan or installment not found."}, status=404)

        if installment.status == 'PAID':
            return Response({"error": "This installment is already fully paid."}, status=400)

        # Create Payment record
        payment = Payment.objects.create(
            loan=loan,
            installment=installment,
            amount=amount,
            method=method,
            reference_number=reference,
            received_by=request.user,
            payment_date=payment_date,
        )

        # Update installment
        installment.amount_paid = (installment.amount_paid or Decimal('0')) + amount
        installment.outstanding = max(Decimal('0'), installment.amount_due - installment.amount_paid)

        if installment.outstanding == 0:
            installment.status = 'PAID'
            installment.paid_at = timezone.now()
        elif installment.amount_paid > 0:
            installment.status = 'PARTIAL'
        installment.save()

        # Update loan outstanding balance
        loan.outstanding_balance = max(Decimal('0'), loan.outstanding_balance - amount)
        if loan.outstanding_balance == 0:
            loan.status = 'CLOSED'
            loan.actual_closure_date = date.today()
        loan.save()

        # Update schedule counters
        schedule = installment.schedule
        if installment.status == 'PAID':
            schedule.installments_paid += 1
            schedule.save()

        # Generate receipt
        receipt = PaymentReceipt.objects.create(
            payment=payment,
            content={
                "loan_number": loan.loan_number,
                "client": f"{loan.client.first_name} {loan.client.last_name}",
                "installment_number": installment.installment_number,
                "due_date": str(installment.due_date),
                "amount_paid": str(amount),
                "method": method,
                "reference": reference,
                "outstanding_after": str(installment.outstanding),
                "loan_balance_after": str(loan.outstanding_balance),
                "received_by": request.user.get_full_name(),
                "payment_date": str(payment_date),
            }
        )

        return Response({
            "message": "Payment recorded successfully.",
            "receipt_number": receipt.receipt_number,
            "installment_status": installment.status,
            "loan_balance": str(loan.outstanding_balance),
            "loan_status": loan.status,
        }, status=status.HTTP_201_CREATED)


class PaymentReceiptView(APIView):
    permission_classes = [IsFinanceStaff]

    def get(self, request, payment_id):
        try:
            receipt = PaymentReceipt.objects.get(payment_id=payment_id)
        except PaymentReceipt.DoesNotExist:
            return Response({"error": "Receipt not found"}, status=404)
        return Response({
            "receipt_number": receipt.receipt_number,
            "generated_at": receipt.generated_at,
            **receipt.content
        })


class LoanBalanceView(APIView):
    permission_classes = [IsLoanOfficer]

    def get(self, request, loan_id):
        try:
            loan = Loan.objects.get(pk=loan_id)
        except Loan.DoesNotExist:
            return Response({"error": "Loan not found"}, status=404)

        try:
            paid_installments = loan.schedule.installments.filter(status='PAID').count()
            overdue_installments = loan.schedule.installments.filter(status='OVERDUE').count()
            total = loan.schedule.total_installments
        except Exception as e:
            return Response({"error": f"Cannot retrieve schedule: {str(e)}"}, status=400)

        return Response({
            "loan_number": loan.loan_number,
            "principal": str(loan.principal_amount),
            "total_repayable": str(loan.total_repayable),
            "outstanding_balance": str(loan.outstanding_balance),
            "amount_repaid": str(loan.total_repayable - loan.outstanding_balance),
            "installments_paid": paid_installments,
            "installments_remaining": total - paid_installments,
            "installments_overdue": overdue_installments,
            "loan_status": loan.status,
            "expected_closure": loan.expected_closure_date,
        })


class TriggerA4ScanView(APIView):
    """Trigger A4 to scan all active loans for overdue installments."""
    permission_classes = [IsCollectionsOfficer]

    def post(self, request):
        active_loans = Loan.objects.filter(status='ACTIVE').prefetch_related(
            'schedule__installments'
        )

        loans_payload = []
        for loan in active_loans:
            try:
                installments = [
                    {
                        "installment_id": i.id,
                        "installment_number": i.installment_number,
                        "due_date": str(i.due_date),
                        "amount_due": float(i.amount_due),
                        "outstanding": float(i.amount_due - i.amount_paid),
                        "status": i.status,
                    }
                    for i in loan.schedule.installments.all()
                    if i.status not in ['PAID', 'WAIVED']
                ]
                loans_payload.append({
                    "loan_id": loan.id,
                    "loan_number": loan.loan_number,
                    "installments": installments
                })
            except Exception:
                continue

        try:
            response = httpx.post(
                f"{settings.AI_SERVICE_URL}/api/a4/check-repayments",
                json={"loans": loans_payload, "today": str(date.today())},
                headers={"x-api-key": settings.AI_SERVICE_API_KEY},
                timeout=30.0
            )
            ai_result = response.json()
        except Exception as e:
            return Response(
                {"error": f"AI service unavailable: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # Update overdue installments in DB
        overdue_cases = ai_result.get("output", {}).get("overdue_cases", [])
        for case in overdue_cases:
            try:
                inst = RepaymentInstallment.objects.get(pk=case["installment_id"])
                inst.status = 'OVERDUE'
                inst.days_overdue = case["days_overdue"]
                inst.save()
            except RepaymentInstallment.DoesNotExist:
                continue

        return Response(ai_result)