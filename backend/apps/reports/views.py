from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import csv
import json
from django.http import HttpResponse

from .services import DashboardService, ExportService
from .models import ReportSnapshot, KPIRecord
from apps.users.permissions import IsAdmin, IsAdminOrBranchManager, IsRiskAnalyst, IsComplianceOfficer


class OverviewDashboardView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        data = DashboardService.get_overview()
        return Response(data)


class PortfolioDashboardView(APIView):
    permission_classes = [IsAdminOrBranchManager]

    def get(self, request):
        data = DashboardService.get_portfolio()
        return Response(data)


class DefaultRateReportView(APIView):
    permission_classes = [IsAdminOrBranchManager]

    def get(self, request):
        data = DashboardService.get_default_rate()
        return Response(data)


class ArrearsReportView(APIView):
    permission_classes = [IsAdminOrBranchManager]

    def get(self, request):
        data = DashboardService.get_arrears_distribution()
        return Response(data)


class RiskDistributionView(APIView):
    permission_classes = [IsRiskAnalyst]

    def get(self, request):
        data = DashboardService.get_risk_distribution()
        return Response(data)


class DisbursementSummaryView(APIView):
    permission_classes = [IsAdminOrBranchManager]

    def get(self, request):
        months = int(request.query_params.get('months', 3))
        data = DashboardService.get_disbursement_summary(months=months)
        return Response(data)


class AgentPerformanceView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        data = DashboardService.get_agent_performance()
        return Response(data)


class FraudReportView(APIView):
    permission_classes = [IsComplianceOfficer]

    def get(self, request):
        data = DashboardService.get_fraud_report()
        return Response(data)


class StaffActivityView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        days = int(request.query_params.get('days', 7))
        data = DashboardService.get_staff_activity(days=days)
        return Response(data)


class RoleBasedDashboardView(APIView):
    """
    Single entry point that returns the correct dashboard
    based on the requesting user's role.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = request.user.role

        if role == 'admin':
            return Response(DashboardService.get_overview())

        elif role in ['branch_manager']:
            portfolio = DashboardService.get_portfolio()
            arrears = DashboardService.get_arrears_distribution()
            default_rate = DashboardService.get_default_rate()
            return Response({**portfolio, **arrears, **default_rate})

        elif role == 'risk_analyst':
            return Response(DashboardService.get_risk_distribution())

        elif role == 'collections_officer':
            return Response(DashboardService.get_arrears_distribution())

        elif role == 'compliance_officer':
            return Response(DashboardService.get_fraud_report())

        elif role == 'finance_staff':
            return Response(DashboardService.get_disbursement_summary())

        else:
            # Loan officers see basic loan pipeline
            from apps.loans.models import LoanApplication
            from django.db.models import Count
            return Response({
                "my_applications": (
                    LoanApplication.objects
                    .filter(created_by=request.user)
                    .values('status')
                    .annotate(count=Count('id'))
                )
            })


class ExportReportView(APIView):
    """
    Export any report as CSV.
    Usage: GET /api/reports/export/?type=portfolio
    """
    permission_classes = [IsAdminOrBranchManager]

    REPORT_MAP = {
        'portfolio': DashboardService.get_portfolio,
        'default_rate': DashboardService.get_default_rate,
        'arrears': DashboardService.get_arrears_distribution,
        'disbursement': DashboardService.get_disbursement_summary,
        'risk_distribution': DashboardService.get_risk_distribution,
        'agent_performance': DashboardService.get_agent_performance,
        'fraud': DashboardService.get_fraud_report,
    }

    EXPORT_MAP = {
        'portfolio': ExportService.get_portfolio,
        'default_rate': ExportService.get_default_rate,
        'arrears': ExportService.get_arrears_distribution,
        'disbursement': ExportService.get_disbursement_summary,
        'risk_distribution': ExportService.get_risk_distribution,
        'agent_performance': ExportService.get_agent_performance,
        'fraud': ExportService.get_fraud_report,
    }

    def get(self, request):
        report_type = request.query_params.get('type', 'portfolio')
        fmt = request.query_params.get('export_format', 'json')

        if report_type not in self.REPORT_MAP:
            return Response({"error": f"Unknown report type: {report_type}"}, status=400)

        if fmt == 'csv':
            data = self.EXPORT_MAP[report_type]()
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = (
                f'attachment; filename="{report_type}_report.csv"'
            )
            writer = csv.writer(response)
            if isinstance(data, list) and data:
                writer.writerow(data[0].keys())
                for row in data:
                    writer.writerow(row.values())
            else:
                writer.writerow(['No data available'])
            return response
            
        if fmt == 'export_json':
            data = self.EXPORT_MAP[report_type]()
            return Response(data)

        data = self.REPORT_MAP[report_type]()

        # Save snapshot
        from datetime import date
        ReportSnapshot.objects.create(
            report_type=report_type.upper(),
            data=data,
            generated_by=request.user.username,
        )

        return Response(data)


class KPIView(APIView):
    """Returns latest KPI values."""
    permission_classes = [IsAdmin]

    def get(self, request):
        from apps.loans.models import Loan, RiskAssessment, AIRecommendation
        from apps.repayments.models import RepaymentInstallment
        from django.db.models import Count, Avg
        from decimal import Decimal

        total_loans = Loan.objects.count()
        defaulted = Loan.objects.filter(status='DEFAULTED').count()
        paid_insts = RepaymentInstallment.objects.filter(status='PAID').count()
        all_insts = RepaymentInstallment.objects.exclude(status='WAIVED').count()
        total_recs = AIRecommendation.objects.count()
        accepted_recs = AIRecommendation.objects.filter(officer_decision='ACCEPTED').count()

        return Response({
            "kpis": {
                "default_rate_percent": round(defaulted / total_loans * 100, 2) if total_loans else 0,
                "repayment_success_rate_percent": round(paid_insts / all_insts * 100, 2) if all_insts else 0,
                "ai_acceptance_rate_percent": round(accepted_recs / total_recs * 100, 2) if total_recs else 0,
                "active_loans": Loan.objects.filter(status='ACTIVE').count(),
                "avg_risk_score": round(
                    RiskAssessment.objects.aggregate(avg=Avg('risk_score'))['avg'] or 0, 1
                ),
            }
        })