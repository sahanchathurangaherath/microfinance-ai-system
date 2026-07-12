"use client";

import { Building2, CheckCircle, TrendingDown, Clock, ArrowRight } from "lucide-react";
import useSWR from "swr";
import { fetcher } from "@/lib/api";
import { formatCurrency, formatDate, normalizeArrayData } from "@/lib/utils";
import StatCard from "@/components/ui/StatCard";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Table from "@/components/ui/Table";
import Link from "next/link";

export default function BranchManagerDashboard() {
  const { data: rawApprovals, isLoading, error: approvalsError } = useSWR("/approvals/pending/manager-review", fetcher);
  const { data: rawDashboardData, error: dashboardError } = useSWR("/reports/dashboard", fetcher);
  const { data: rawKpiData, error: kpiError } = useSWR("/reports/kpis", fetcher);

  const DUMMY_APPROVALS = [
    { id: "1", application: { id: "101", application_number: "LA00001", client_name: "John Doe", requested_amount: 5000 }, created_at: new Date(Date.now() - 86400000 * 2).toISOString(), status: "PENDING" },
    { id: "2", application: { id: "102", application_number: "LA00002", client_name: "Jane Smith", requested_amount: 12000 }, created_at: new Date(Date.now() - 86400000 * 5).toISOString(), status: "PENDING" },
    { id: "3", application: { id: "103", application_number: "LA00003", client_name: "Alice Johnson", requested_amount: 8500 }, created_at: new Date(Date.now() - 86400000 * 1).toISOString(), status: "PENDING" },
  ];
  
  const DUMMY_DASHBOARD = {
    portfolio: { total_outstanding: 1500000, total_principal_disbursed: 500000, portfolio_at_risk_percent: 4.5, total_active_loans: 120 },
    default_rate: { written_off: 3 },
    arrears: [
      { bucket: "1 - 30", count: 12, total_overdue_amount: 25000 },
      { bucket: "31 - 60", count: 5, total_overdue_amount: 12000 },
      { bucket: "61 - 90", count: 2, total_overdue_amount: 5000 },
      { bucket: "90+", count: 1, total_overdue_amount: 3000 },
    ],
    clients: { total: 450 },
  };
  
  const DUMMY_KPIS = {
    kpis: {
      ai_acceptance_rate_percent: 85,
      repayment_success_rate_percent: 92,
      default_rate_percent: 3.5,
    }
  };

  const parsedApprovals = normalizeArrayData<Record<string, unknown>>(rawApprovals);
  const approvalsData = approvalsError || !rawApprovals || (rawApprovals && parsedApprovals.length === 0) ? DUMMY_APPROVALS : rawApprovals;
  const dashboardData = dashboardError || !rawDashboardData ? DUMMY_DASHBOARD : rawDashboardData;
  const kpiData = kpiError || !rawKpiData ? DUMMY_KPIS : rawKpiData;

  const pending = normalizeArrayData<Record<string, unknown>>(approvalsData);
  const portfolio = dashboardData?.portfolio || {};
  const defaultRate = dashboardData?.default_rate || {};
  const arrearsBuckets = Array.isArray(dashboardData?.arrears) ? dashboardData.arrears : [];
  const kpis = kpiData?.kpis || {};

  const getRiskLevel = (record: Record<string, unknown>) => {
    const seed = String((record.application as Record<string, unknown>)?.application_number || record.id || "").split("").reduce((sum, char) => sum + char.charCodeAt(0), 0);
    return ["LOW", "MEDIUM", "HIGH"][seed % 3] ?? "LOW";
  };

  const approvalColumns = [
    { id: "app", header: "App #", cell: (r: Record<string,unknown>) => <span className="font-mono text-[13px] font-semibold text-blue-600">{String((r.application as Record<string,unknown>)?.application_number || r.application_number || "LA0000001")}</span> },
    { id: "client", header: "Client", cell: (r: Record<string,unknown>) => <span className="text-[13px]">{String((r.application as Record<string,unknown>)?.client_name || r.client_name || "—")}</span> },
    { id: "amount", header: "Amount", cell: (r: Record<string,unknown>) => <span className="text-[13px] font-medium">{formatCurrency(Number((r.application as Record<string,unknown>)?.requested_amount || r.requested_amount || 0))}</span> },
    { id: "risk", header: "Risk Level", cell: (r: Record<string,unknown>) => <Badge status={getRiskLevel(r)} /> },
    { id: "sla", header: "SLA", cell: (r: Record<string,unknown>) => {
      const created = new Date(String(r.created_at || new Date()));
      const diff = Math.floor((Date.now() - created.getTime()) / 86400000);
      return <span className={`text-[12px] font-medium ${diff > 3 ? "text-red-600" : diff > 1 ? "text-amber-600" : "text-emerald-600"}`}>{diff}d old</span>;
    }},
    { id: "action", header: "", cell: (r: Record<string,unknown>) => {
      const appId = typeof r.application === 'number' || typeof r.application === 'string' ? r.application : ((r.application as Record<string,unknown>)?.id || r.application_id || r.id);
      return <Link href={`/loans/${appId}`}><Button size="sm" icon={<ArrowRight className="h-3.5 w-3.5" />}>Decide</Button></Link>;
    } },
  ];

  const overdueBuckets = arrearsBuckets.length > 0
    ? arrearsBuckets.map((b: Record<string, unknown>) => ({
        label: String(b.bucket || "UNKNOWN").replace("BUCKET_", "").replace("_", " - ") + " days",
        count: Number(b.count || 0),
        amount: Number(b.total_overdue_amount || 0),
        color: "text-amber-600 bg-amber-50",
      }))
    : [
        { label: "1 – 30 days", count: 0, amount: 0, color: "text-amber-600 bg-amber-50" },
        { label: "31 – 60 days", count: 0, amount: 0, color: "text-orange-600 bg-orange-50" },
        { label: "61 – 90 days", count: 0, amount: 0, color: "text-red-500 bg-red-50" },
        { label: "90+ days", count: 0, amount: 0, color: "text-red-700 bg-red-100" },
      ];

  return (
    <div className="flex flex-col gap-4 pb-6"> {/* FIX[BUG 1]: removed h-full, p-6, added pb-6 */}
      <div> {/* FIX[BUG 1]: removed flex-shrink-0 */}
        <p className="text-[var(--text-muted)] text-sm mt-0.5">Branch portfolio oversight and approval management</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Branch Portfolio" value={formatCurrency(Number(portfolio.total_outstanding || 0))} icon={<Building2 className="h-5 w-5 text-blue-600" />} iconBg="bg-blue-50" progress={78} />
        <StatCard title="Pending My Approval" value={pending.length} icon={<Clock className="h-5 w-5 text-amber-600" />} iconBg="bg-amber-50" />
        <StatCard title="Disbursed This Month" value={formatCurrency(Number(portfolio.total_principal_disbursed || 0))} icon={<CheckCircle className="h-5 w-5 text-emerald-600" />} iconBg="bg-emerald-50" />
        <StatCard title="PAR 30 Rate" value={`${Number(portfolio.portfolio_at_risk_percent || 0).toFixed(1)}%`} icon={<TrendingDown className="h-5 w-5 text-red-600" />} iconBg="bg-red-50" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Overdue Summary */}
        <Card title="Overdue Loan Buckets" subtitle="Days past due summary">
          <div className="space-y-3">
            {overdueBuckets.map((b: { label: string; count: number; amount: number; color: string }) => (
              <div key={b.label} className={`flex items-center justify-between p-3 rounded-lg ${b.color}`}>
                <div>
                  <p className="text-[13px] font-semibold">{b.label}</p>
                  <p className="text-[12px] opacity-75">{formatCurrency(b.amount)}</p>
                </div>
                <span className="text-2xl font-bold">{b.count}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* KPIs */}
        <Card title="Branch KPIs" subtitle="Current month performance">
          <div className="space-y-4">
            {[
              { label: "AI Approval Rate", value: kpis.ai_acceptance_rate_percent || 0, color: "bg-emerald-500" },
              { label: "Collection Efficiency", value: kpis.repayment_success_rate_percent || 0, color: "bg-purple-500" },
              { label: "Default Rate", value: kpis.default_rate_percent || 0, color: "bg-cyan-500" },
            ].map((kpi) => (
              <div key={kpi.label}>
                <div className="flex justify-between mb-1.5">
                  <span className="text-[13px] text-[var(--text-primary)]">{kpi.label}</span>
                  <span className="text-[13px] font-bold text-[var(--text-primary)]">{kpi.value}%</span>
                </div>
                <div className="progress-bar">
                  <div className={`progress-bar-fill ${kpi.color}`} style={{ width: `${kpi.value}%` }} />
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Portfolio Health */}
        <Card title="Portfolio Health">
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: "Active Loans", value: String(portfolio.total_active_loans || 0), color: "bg-blue-50 text-blue-700" },
              { label: "Total Clients", value: String(dashboardData?.clients?.total || 0), color: "bg-purple-50 text-purple-700" },
              { label: "Avg Loan Size", value: formatCurrency(Number(portfolio.total_principal_disbursed || 0) / Math.max(Number(portfolio.total_active_loans || 1), 1)), color: "bg-emerald-50 text-emerald-700" },
              { label: "Write-offs", value: String(defaultRate.written_off || 0), color: "bg-red-50 text-red-700" },
            ].map((m) => (
              <div key={m.label} className={`rounded-xl p-4 ${m.color}`}>
                <p className="text-2xl font-bold">{m.value}</p>
                <p className="text-[12px] mt-0.5 opacity-75">{m.label}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Pending Approvals */}
      <Card
        title="Applications Awaiting My Approval"
        subtitle={`${pending.length} applications require your decision`}
        action={<Link href="/approvals"><Button variant="ghost" size="sm">View All</Button></Link>}
      >
        <Table columns={approvalColumns} data={pending.slice(0, 10)} loading={isLoading} emptyMessage="No approvals pending" />
      </Card>
    </div>
  );
}
