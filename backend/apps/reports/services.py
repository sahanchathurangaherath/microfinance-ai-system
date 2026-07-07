from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal


class DashboardService:
    """
    Centralized query layer for all dashboard and report data.
    All methods return plain dicts — easy to serialize and cache.
    """

    @staticmethod
    def get_overview():
        """System-wide overview for Admin."""
        from apps.clients.models import Client
        from apps.loans.models import LoanApplication, Loan
        from apps.repayments.models import RepaymentInstallment
        from apps.fraud.models import FraudAlert
        from apps.collections.models import DelinquencyCase

        today = date.today()
        this_month_start = today.replace(day=1)

        return {
            "generated_at": timezone.now().isoformat(),
            "clients": {
                "total": Client.objects.count(),
                "verified": Client.objects.filter(status='VERIFIED').count(),
                "pending_kyc": Client.objects.filter(status='PENDING').count(),
                "active": Client.objects.filter(status='ACTIVE').count(),
            },
            "applications": {
                "total": LoanApplication.objects.count(),
                "this_month": LoanApplication.objects.filter(
                    created_at__date__gte=this_month_start
                ).count(),
                "by_status": dict(
                    LoanApplication.objects.values('status')
                    .annotate(count=Count('id'))
                    .values_list('status', 'count')
                ),
            },
            "loans": {
                "active": Loan.objects.filter(status='ACTIVE').count(),
                "closed_this_month": Loan.objects.filter(
                    status='CLOSED',
                    actual_closure_date__gte=this_month_start
                ).count(),
                "defaulted": Loan.objects.filter(status='DEFAULTED').count(),
                "total_outstanding": str(
                    Loan.objects.filter(status='ACTIVE')
                    .aggregate(total=Sum('outstanding_balance'))['total'] or Decimal('0')
                ),
            },
            "collections": {
                "open_cases": DelinquencyCase.objects.filter(status='OPEN').count(),
                "in_progress": DelinquencyCase.objects.filter(status='IN_PROGRESS').count(),
                "escalated": DelinquencyCase.objects.filter(status='ESCALATED').count(),
            },
            "fraud": {
                "open_alerts": FraudAlert.objects.filter(status='OPEN').count(),
                "under_investigation": FraudAlert.objects.filter(
                    status='UNDER_INVESTIGATION'
                ).count(),
                "confirmed_this_month": FraudAlert.objects.filter(
                    status='CONFIRMED',
                    triggered_at__date__gte=this_month_start
                ).count(),
            },
        }

    @staticmethod
    def get_portfolio():
        """Portfolio health for Branch Managers."""
        from apps.loans.models import Loan
        from apps.repayments.models import RepaymentInstallment

        active_loans = Loan.objects.filter(status='ACTIVE')
        total_principal = active_loans.aggregate(
            total=Sum('principal_amount')
        )['total'] or Decimal('0')
        total_outstanding = active_loans.aggregate(
            total=Sum('outstanding_balance')
        )['total'] or Decimal('0')

        overdue_loan_ids = RepaymentInstallment.objects.filter(
            status='OVERDUE'
        ).values_list('schedule__loan_id', flat=True).distinct()

        overdue_count = len(overdue_loan_ids)
        total_count = active_loans.count()
        par_rate = round(overdue_count / total_count * 100, 2) if total_count > 0 else 0

        return {
            "portfolio": {
                "total_active_loans": total_count,
                "total_principal_disbursed": str(total_principal),
                "total_outstanding": str(total_outstanding),
                "total_repaid": str(total_principal - total_outstanding),
                "portfolio_at_risk_count": overdue_count,
                "portfolio_at_risk_percent": par_rate,
            }
        }

    @staticmethod
    def get_default_rate():
        """Default and write-off rate report."""
        from apps.loans.models import Loan

        total = Loan.objects.count()
        defaulted = Loan.objects.filter(status='DEFAULTED').count()
        written_off = Loan.objects.filter(status='WRITTEN_OFF').count()
        closed = Loan.objects.filter(status='CLOSED').count()

        default_rate = round(defaulted / total * 100, 2) if total > 0 else 0

        return {
            "default_rate": {
                "total_loans": total,
                "active": Loan.objects.filter(status='ACTIVE').count(),
                "closed": closed,
                "defaulted": defaulted,
                "written_off": written_off,
                "default_rate_percent": default_rate,
            }
        }

    @staticmethod
    def get_arrears_distribution():
        """Arrears bucket breakdown for Collections team."""
        from apps.collections.models import DelinquencyCase

        buckets = DelinquencyCase.objects.exclude(
            status__in=['RESOLVED', 'WRITTEN_OFF']
        ).values('bucket').annotate(
            count=Count('id'),
            total_overdue=Sum('total_overdue_amount')
        )

        return {
            "arrears": [
                {
                    "bucket": b['bucket'],
                    "count": b['count'],
                    "total_overdue_amount": str(b['total_overdue'] or 0),
                }
                for b in buckets
            ]
        }

    @staticmethod
    def get_risk_distribution():
        """Risk score distribution for Risk Analysts."""
        from apps.loans.models import RiskAssessment

        dist = RiskAssessment.objects.values('risk_category').annotate(
            count=Count('id'),
            avg_score=Avg('risk_score')
        )

        score_ranges = {
            "0-39": RiskAssessment.objects.filter(risk_score__lt=40).count(),
            "40-69": RiskAssessment.objects.filter(
                risk_score__gte=40, risk_score__lt=70
            ).count(),
            "70-100": RiskAssessment.objects.filter(risk_score__gte=70).count(),
        }

        return {
            "risk_distribution": {
                "by_category": [
                    {
                        "category": d['risk_category'],
                        "count": d['count'],
                        "avg_score": round(d['avg_score'], 1),
                    }
                    for d in dist
                ],
                "by_score_range": score_ranges,
                "avg_score_overall": round(
                    RiskAssessment.objects.aggregate(avg=Avg('risk_score'))['avg'] or 0, 1
                ),
            }
        }

    @staticmethod
    def get_disbursement_summary(months=3):
        """Disbursement volume over last N months."""
        from apps.loans.models import Loan
        from django.db.models.functions import TruncMonth

        cutoff = date.today() - timedelta(days=30 * months)
        by_month = (
            Loan.objects.filter(disbursed_at__date__gte=cutoff)
            .annotate(month=TruncMonth('disbursed_at'))
            .values('month')
            .annotate(count=Count('id'), total=Sum('principal_amount'))
            .order_by('month')
        )

        return {
            "disbursements": [
                {
                    "month": str(row['month'].date())[:7],
                    "count": row['count'],
                    "total_amount": str(row['total'] or 0),
                }
                for row in by_month
            ]
        }

    @staticmethod
    def get_agent_performance():
        """AI agent action statistics for Admin review."""
        from apps.audit.models import AgentActionLog
        from apps.loans.models import RiskAssessment, AIRecommendation

        risk_stats = RiskAssessment.objects.aggregate(
            total=Count('id'),
            avg_confidence=Avg('confidence'),
            avg_score=Avg('risk_score'),
        )

        rec_stats = {
            "total": AIRecommendation.objects.count(),
            "accepted": AIRecommendation.objects.filter(
                officer_decision='ACCEPTED'
            ).count(),
            "overridden": AIRecommendation.objects.filter(
                officer_decision='OVERRIDDEN'
            ).count(),
        }
        total_recs = rec_stats['total']
        acceptance_rate = round(
            rec_stats['accepted'] / total_recs * 100, 1
        ) if total_recs > 0 else 0

        return {
            "agent_performance": {
                "A2_risk_assessment": {
                    "total_assessments": risk_stats['total'],
                    "avg_confidence": round(risk_stats['avg_confidence'] or 0, 2),
                    "avg_risk_score": round(risk_stats['avg_score'] or 0, 1),
                },
                "A3_recommendation": {
                    "total_recommendations": rec_stats['total'],
                    "accepted": rec_stats['accepted'],
                    "overridden": rec_stats['overridden'],
                    "acceptance_rate_percent": acceptance_rate,
                },
            }
        }

    @staticmethod
    def get_fraud_report():
        """Fraud alert summary for Compliance Officers."""
        from apps.fraud.models import FraudAlert

        by_type = FraudAlert.objects.values('alert_type', 'severity').annotate(
            count=Count('id')
        )
        by_status = dict(
            FraudAlert.objects.values('status')
            .annotate(count=Count('id'))
            .values_list('status', 'count')
        )

        return {
            "fraud_summary": {
                "by_status": by_status,
                "by_type_and_severity": list(by_type),
                "avg_risk_score": round(
                    FraudAlert.objects.aggregate(
                        avg=Avg('fraud_risk_score')
                    )['avg'] or 0, 1
                ),
            }
        }

    @staticmethod
    def get_loan_officer_dashboard(user):
        """Personalised dashboard for a Loan Officer."""
        from apps.loans.models import LoanApplication
        from apps.clients.models import Client

        today = date.today()
        this_month_start = today.replace(day=1)

        # Applications created by this officer
        my_apps = LoanApplication.objects.filter(created_by=user)
        total_apps = my_apps.count()

        by_status = dict(
            my_apps.values('status')
            .annotate(count=Count('id'))
            .values_list('status', 'count')
        )

        # Clients registered by this officer
        clients_total = Client.objects.filter(registered_by=user).count()
        clients_this_month = Client.objects.filter(
            registered_by=user,
            created_at__date__gte=this_month_start
        ).count()

        approved_this_month = my_apps.filter(
            status='APPROVED',
            updated_at__date__gte=this_month_start
        ).count()
        rejected_this_month = my_apps.filter(
            status='REJECTED',
            updated_at__date__gte=this_month_start
        ).count()

        return {
            "generated_at": today.isoformat(),
            "clients": {
                "active": clients_total,
                "this_month": clients_this_month,
            },
            "loans": {
                "active": by_status.get('APPROVED', 0) + by_status.get('DISBURSED', 0),
                "total_outstanding": "0",  # officer-level not tracked separately
            },
            "default_rate": {
                "default_rate_percent": 0,
            },
            "applications": {
                "total": total_apps,
                "draft": by_status.get('DRAFT', 0),
                "submitted": by_status.get('SUBMITTED', 0),
                "approved_this_month": approved_this_month,
                "rejected_this_month": rejected_this_month,
                "by_status": by_status,
            },
        }

    @staticmethod
    def get_staff_activity(days=7):
        """Staff login and action counts for Admin."""
        from apps.users.models import User, UserActivityLog
        from django.db.models import Count

        cutoff = timezone.now() - timedelta(days=days)
        activity = (
            UserActivityLog.objects.filter(timestamp__gte=cutoff)
            .values('user__username', 'user__role', 'action')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        return {
            "staff_activity": {
                "period_days": days,
                "activities": list(activity),
            }
        }


class ExportService:
    """
    Dedicated service for exporting raw database rows for CSV downloads,
    rather than aggregated dashboard stats.
    """

    @staticmethod
    def get_portfolio():
        from apps.loans.models import Loan
        return list(Loan.objects.filter(status='ACTIVE').values(
            'id', 'client__client_number', 'principal_amount', 
            'outstanding_balance', 'interest_rate', 'disbursed_at', 'expected_closure_date'
        ))

    @staticmethod
    def get_default_rate():
        from apps.loans.models import Loan
        return list(Loan.objects.values(
            'id', 'client__client_number', 'status', 
            'principal_amount', 'outstanding_balance', 'disbursed_at', 'actual_closure_date'
        ))

    @staticmethod
    def get_arrears_distribution():
        from apps.collections.models import DelinquencyCase
        return list(DelinquencyCase.objects.exclude(
            status__in=['RESOLVED', 'WRITTEN_OFF']
        ).values(
            'id', 'loan__id', 'loan__client__client_number', 
            'bucket', 'total_overdue_amount', 'days_overdue', 'status', 'opened_at'
        ))

    @staticmethod
    def get_disbursement_summary():
        from apps.loans.models import Loan
        return list(Loan.objects.exclude(disbursed_at__isnull=True).values(
            'id', 'client__client_number', 'principal_amount', 
            'disbursed_at', 'status'
        ))

    @staticmethod
    def get_risk_distribution():
        from apps.loans.models import RiskAssessment
        return list(RiskAssessment.objects.values(
            'id', 'application__id', 'application__client__client_number',
            'risk_score', 'risk_category', 'confidence', 'generated_at'
        ))

    @staticmethod
    def get_agent_performance():
        from apps.loans.models import AIRecommendation
        return list(AIRecommendation.objects.values(
            'id', 'application__id', 'recommendation_type', 'confidence', 
            'officer_decision', 'generated_at'
        ))

    @staticmethod
    def get_fraud_report():
        from apps.fraud.models import FraudAlert
        return list(FraudAlert.objects.values(
            'id', 'alert_type', 'severity', 'status', 'fraud_risk_score', 
            'triggered_at'
        ))