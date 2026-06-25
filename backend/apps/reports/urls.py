from django.urls import path
from .views import (
    OverviewDashboardView, PortfolioDashboardView, DefaultRateReportView,
    ArrearsReportView, RiskDistributionView, DisbursementSummaryView,
    AgentPerformanceView, FraudReportView, StaffActivityView,
    RoleBasedDashboardView, ExportReportView, KPIView
)

urlpatterns = [
    path('dashboard/', RoleBasedDashboardView.as_view()),
    path('dashboard/overview/', OverviewDashboardView.as_view()),
    path('dashboard/portfolio/', PortfolioDashboardView.as_view()),
    path('default-rate/', DefaultRateReportView.as_view()),
    path('arrears/', ArrearsReportView.as_view()),
    path('risk-distribution/', RiskDistributionView.as_view()),
    path('disbursements/', DisbursementSummaryView.as_view()),
    path('agent-performance/', AgentPerformanceView.as_view()),
    path('fraud/', FraudReportView.as_view()),
    path('staff-activity/', StaffActivityView.as_view()),
    path('export/', ExportReportView.as_view()),
    path('kpis/', KPIView.as_view()),
]