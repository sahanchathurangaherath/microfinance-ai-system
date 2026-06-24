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
    path('reports/default-rate/', DefaultRateReportView.as_view()),
    path('reports/arrears/', ArrearsReportView.as_view()),
    path('reports/risk-distribution/', RiskDistributionView.as_view()),
    path('reports/disbursements/', DisbursementSummaryView.as_view()),
    path('reports/agent-performance/', AgentPerformanceView.as_view()),
    path('reports/fraud/', FraudReportView.as_view()),
    path('reports/staff-activity/', StaffActivityView.as_view()),
    path('reports/export/', ExportReportView.as_view()),
    path('reports/kpis/', KPIView.as_view()),
]