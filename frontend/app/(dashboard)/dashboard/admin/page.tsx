"use client";

import { Users, FileText, AlertTriangle, TrendingUp, UserCog, Shield, Plus, Activity } from "lucide-react";
import useSWR from "swr";
import { fetcher } from "@/lib/api";
import { formatCurrency, formatRelativeTime } from "@/lib/utils";
import StatCard from "@/components/ui/StatCard";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Table from "@/components/ui/Table";
import Link from "next/link";

export default function AdminDashboard() {
  const { data: users, isLoading: usersLoading } = useSWR("/users", fetcher);
  const { data: loans, isLoading: loansLoading } = useSWR("/loans/applications", fetcher);
  const { data: fraud, isLoading: fraudLoading } = useSWR("/fraud/alerts", fetcher);
  const { data: audit, error: auditError, isLoading: auditLoading, mutate: mutateAudit } = useSWR("/audit/logs", fetcher);
  const { data: overviewData, isLoading: overviewLoading } = useSWR("/reports/dashboard/overview", fetcher);

  const userItems = Array.isArray(users?.results)
    ? (users.results as Record<string, unknown>[])
    : Array.isArray(users)
    ? (users as Record<string, unknown>[])
    : [];
  const loanItems = Array.isArray(loans?.results)
    ? (loans.results as Record<string, unknown>[])
    : Array.isArray(loans)
    ? (loans as Record<string, unknown>[])
    : [];
  const auditItems = Array.isArray(audit?.results)
    ? (audit.results as Record<string, unknown>[])
    : Array.isArray(audit)
    ? (audit as Record<string, unknown>[])
    : [];

  const fraudAlertsList = Array.isArray(fraud?.results)
    ? (fraud.results as Record<string, unknown>[])
    : Array.isArray(fraud)
    ? (fraud as Record<string, unknown>[])
    : [];

  const totalUsers = users?.count ?? userItems.length ?? 0;
  const activeLoans = loanItems.filter((loan) => String(loan.status || "").toUpperCase() !== "DRAFT").length || overviewData?.loans?.active || 0;
  const fraudAlerts = Number(overviewData?.fraud?.open_alerts ?? fraud?.count ?? fraudAlertsList.length ?? 0);
  const portfolioValue = Number(overviewData?.loans?.total_outstanding || 0);

  const roleDistribution = [
    { role: "Loan Officer", key: "loan_officer", color: "bg-blue-500" },
    { role: "Risk Analyst", key: "risk_analyst", color: "bg-purple-500" },
    { role: "Branch Manager", key: "branch_manager", color: "bg-emerald-500" },
    { role: "Collections", key: "collections_officer", color: "bg-amber-500" },
    { role: "Finance Staff", key: "finance_staff", color: "bg-cyan-500" },
    { role: "Compliance", key: "compliance_officer", color: "bg-red-500" },
  ].map((entry) => ({
    ...entry,
    count: userItems.filter((user) => String(user.role || "").toLowerCase() === entry.key).length,
  }));

  const loansByStatus = [
    { label: "Draft", status: "DRAFT", color: "bg-gray-300" },
    { label: "Submitted", status: "SUBMITTED", color: "bg-amber-400" },
    { label: "AI Screening", status: "AI_SCREENING", color: "bg-blue-400" },
    { label: "Under Review", status: "RISK_REVIEWED", color: "bg-purple-400" },
    { label: "Approved", status: "APPROVED", color: "bg-emerald-400" },
    { label: "Rejected", status: "REJECTED", color: "bg-red-400" },
  ].map((s) => {
    let count = 0;
    if (s.status === "RISK_REVIEWED") {
      count = loanItems.filter((l) => ["RISK_REVIEWED", "MANAGER_REVIEW", "COMMITTEE_REVIEW"].includes(String(l.status || "").toUpperCase())).length;
    } else {
      count = loanItems.filter((l) => String(l.status || "").toUpperCase() === s.status).length;
    }
    return { ...s, count };
  });

  const recentAuditColumns = [
    { id: "user", header: "User", cell: (row: Record<string, unknown>) => <span className="text-sm text-gray-700">{String(row.user_name || row.username || "-")}</span> },
    { id: "action", header: "Action", cell: (row: Record<string, unknown>) => <Badge status={String(row.action_type || "LOGIN")} /> },
    { id: "desc", header: "Description", cell: (row: Record<string, unknown>) => <span className="text-sm text-gray-600 truncate max-w-xs block">{String(row.description || "-")}</span> },
    { id: "time", header: "Time", cell: (row: Record<string, unknown>) => <span className="text-xs text-gray-400">{formatRelativeTime(String(row.timestamp))}</span> },
  ];

  return (
    <div className="flex flex-col gap-4 pb-6"> {/* FIX[BUG 1]: removed h-full, added pb-6 */}
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"> {/* FIX[BUG 1]: removed flex-shrink-0 */}
        <div>
          <p className="text-[var(--text-muted)] text-sm mt-0.5">Full system overview and management</p>
        </div>
        <Link href="/users?new=true">
          <Button icon={<Plus className="h-4 w-4" />}>Add Staff</Button>
        </Link>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard title="Total Staff Users" value={totalUsers} loading={usersLoading} icon={<Users className="h-5 w-5 text-blue-600" />} iconBg="bg-blue-50" />
        <StatCard title="Active Loans" value={activeLoans} loading={loansLoading || overviewLoading} icon={<FileText className="h-5 w-5 text-emerald-600" />} iconBg="bg-emerald-50" />
        <StatCard title="Portfolio Value" value={formatCurrency(Number(overviewData?.loans?.total_outstanding || 0))} loading={overviewLoading} icon={<TrendingUp className="h-5 w-5 text-purple-600" />} iconBg="bg-purple-50" />
        <StatCard title="Open Fraud Alerts" value={fraudAlerts} loading={fraudLoading || overviewLoading} icon={<AlertTriangle className="h-5 w-5 text-red-600" />} iconBg="bg-red-50" />
      </div>

      {/* Middle Row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* User Distribution */}
        <Card title="Staff by Role" subtitle="Active personnel">
          <div className="space-y-3">
            {roleDistribution.map((r) => (
              <div key={r.role} className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${r.color} flex-shrink-0`} />
                <span className="text-[13px] text-[var(--text-primary)] flex-1">{r.role}</span>
                <span className="text-[13px] font-semibold text-[var(--text-primary)]">{r.count}</span>
                <div className="w-20 h-1.5 rounded-full bg-gray-100 overflow-hidden">
                  <div className={`h-full rounded-full ${r.color}`} style={{ width: `${(r.count / Math.max(1, totalUsers)) * 100}%` }} />
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Quick Actions */}
        <Card title="Quick Actions" subtitle="Common administrative tasks">
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: "Create User", href: "/users/new", icon: <UserCog className="h-5 w-5 text-blue-600" />, bg: "bg-blue-50" },
              { label: "Audit Trail", href: "/audit", icon: <Shield className="h-5 w-5 text-purple-600" />, bg: "bg-purple-50" },
              { label: "Fraud Alerts", href: "/fraud", icon: <AlertTriangle className="h-5 w-5 text-red-600" />, bg: "bg-red-50" },
              { label: "All Reports", href: "/reports", icon: <Activity className="h-5 w-5 text-emerald-600" />, bg: "bg-emerald-50" },
            ].map((a) => (
              <Link key={a.label} href={a.href} className="flex items-center gap-3 p-3 rounded-xl border border-[var(--border-color)] hover:border-blue-200 hover:bg-blue-50/30 transition-all group">
                <div className={`w-10 h-10 rounded-lg ${a.bg} flex items-center justify-center flex-shrink-0`}>{a.icon}</div>
                <span className="text-[13px] font-medium text-[var(--text-primary)]">{a.label}</span>
              </Link>
            ))}
          </div>
        </Card>

        {/* Loan Status Summary */}
        <Card title="Loans by Status" subtitle="System-wide pipeline">
          <div className="space-y-2.5">
            {loansByStatus.map((s) => (
              <div key={s.label} className="flex items-center gap-2 text-[13px]">
                <div className={`w-2 h-2 rounded-full ${s.color}`} />
                <span className="flex-1 text-[var(--text-primary)]">{s.label}</span>
                <span className="font-semibold text-[var(--text-primary)]">{s.count}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Audit Log */}
      <Card title="Recent System Activity" subtitle="Latest audit trail entries" action={<Link href="/audit"><Button variant="ghost" size="sm">View All</Button></Link>}>
        <Table columns={recentAuditColumns} data={auditItems} loading={auditLoading} error={auditError} onRetry={() => mutateAudit()} emptyMessage="No recent activity" />
      </Card>
    </div>
  );
}
