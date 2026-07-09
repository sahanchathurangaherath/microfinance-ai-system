"use client";

import { Shield, AlertTriangle, Eye, Clock } from "lucide-react";
import useSWR from "swr";
import { fetcher } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";
import StatCard from "@/components/ui/StatCard";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Table from "@/components/ui/Table";
import Link from "next/link";

export default function ComplianceDashboard() {
  const { data: fraud } = useSWR("/fraud/alerts", fetcher);
  const { data: audit } = useSWR("/audit/logs", fetcher);
  const { data: fraudReport } = useSWR("/reports/fraud", fetcher);
  const { data: kycData } = useSWR("/clients", fetcher);

  const fraudAlerts = fraud?.results || fraud || [];
  const auditLogs = audit?.results || audit || [];
  const kycItems = kycData?.results || kycData || [];
  const fraudSummary = fraudReport?.fraud_summary || {};
  const pendingKyc = Array.isArray(kycItems)
    ? kycItems.filter((item: Record<string, unknown>) => String(item.status || "").toUpperCase() === "PENDING").length
    : 0;
  const openedAlerts = Array.isArray(fraudAlerts) ? fraudAlerts.length : 0;

  const fraudTypeStats = fraudAlerts.reduce((acc: Record<string, {count: number, sev: string}>, curr: Record<string, unknown>) => {
    const type = String(curr.alert_type || "UNKNOWN").replace(/_/g, " ");
    if (!acc[type]) acc[type] = { count: 0, sev: String(curr.severity || "HIGH") };
    acc[type].count += 1;
    return acc;
  }, {});

  const fraudTypes = Object.keys(fraudTypeStats).map(key => ({
    type: key,
    count: fraudTypeStats[key].count,
    sev: fraudTypeStats[key].sev
  })).sort((a, b) => b.count - a.count).slice(0, 5);

  const permissionChanges = auditLogs
    .filter((log: Record<string, unknown>) => String(log.description || "").toLowerCase().includes("permission") || String(log.description || "").toLowerCase().includes("role"))
    .slice(0, 4)
    .map((log: Record<string, unknown>) => ({
      user: String(log.user_name || log.username || "System"),
      change: String(log.description || "Permissions updated"),
      by: String(log.user_name || log.username || "admin"),
      time: formatRelativeTime(String(log.timestamp || new Date()))
    }));

  const fraudColumns = [
    { id: "type", header: "Alert Type", cell: (r: Record<string,unknown>) => <span className="text-[13px] font-medium">{String(r.alert_type || "DUPLICATE_NIC").replace(/_/g, " ")}</span> },
    { id: "client", header: "Client", cell: (r: Record<string,unknown>) => <span className="text-[13px]">{String(r.client_name || "—")}</span> },
    { id: "severity", header: "Severity", cell: (r: Record<string,unknown>) => <Badge status={String(r.severity || "HIGH")} /> },
    { id: "date", header: "Flagged", cell: (r: Record<string,unknown>) => <span className="text-[12px] text-gray-400">{formatRelativeTime(String(r.triggered_at || new Date()))}</span> },
    { id: "status", header: "Status", cell: (r: Record<string,unknown>) => <Badge status={String(r.is_resolved ? "ACTIVE" : "PENDING")} /> },
    { id: "action", header: "", cell: (r: Record<string,unknown>) => <Link href={`/fraud/${r.id}`}><Button size="sm" variant="outline">Review</Button></Link> },
  ];

  const auditColumns = [
    { id: "user", header: "User", accessor: "username" as const },
    { id: "action", header: "Action", cell: (r: Record<string,unknown>) => <Badge status={String(r.action_type || "LOGIN")} /> },
    { id: "desc", header: "Description", cell: (r: Record<string,unknown>) => <span className="text-[13px] text-gray-600 truncate max-w-xs block">{String(r.description || "—")}</span> },
    { id: "ip", header: "IP Address", cell: (r: Record<string,unknown>) => <span className="font-mono text-[12px] text-gray-400">{String(r.ip_address || "—")}</span> },
    { id: "time", header: "Time", cell: (r: Record<string,unknown>) => <span className="text-[12px] text-gray-400">{formatRelativeTime(String(r.timestamp || new Date()))}</span> },
  ];

  return (
    <div className="flex flex-col gap-4 pb-6"> {/* FIX[BUG 1]: removed h-full, p-6, added pb-6 */}
      <div> {/* FIX[BUG 1]: removed flex-shrink-0 */}
        <p className="text-[var(--text-muted)] text-sm mt-0.5">Monitor fraud alerts, audit trails, and KYC compliance</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Open Fraud Alerts" value={openedAlerts} change={3} changeLabel="new today" trend="down" icon={<AlertTriangle className="h-5 w-5 text-red-600" />} iconBg="bg-red-50" />
        <StatCard title="KYC Pending Verification" value={pendingKyc} icon={<Eye className="h-5 w-5 text-amber-600" />} iconBg="bg-amber-50" trend="neutral" />
        <StatCard title="Audit Events Today" value={auditLogs.length} change={12} trend="up" icon={<Shield className="h-5 w-5 text-blue-600" />} iconBg="bg-blue-50" />
        <StatCard title="Permission Changes (Week)" value={auditLogs.filter((item: Record<string, unknown>) => String(item.description || "").toLowerCase().includes("permission")).length} change={-2} trend="up" icon={<Clock className="h-5 w-5 text-purple-600" />} iconBg="bg-purple-50" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card title="Compliance Overview">
          <div className="space-y-3">
            {[
              { label: "KYC Completion Rate", value: Math.max(0, Math.min(100, Math.round((pendingKyc > 0 ? 100 - (pendingKyc / Math.max(kycItems.length || 1, 1)) * 100 : 100)))) , color: "bg-emerald-500" },
              { label: "Fraud Detection Rate", value: Number(fraudSummary.avg_risk_score || 0), color: "bg-blue-500" },
              { label: "AML Screening Coverage", value: 100, color: "bg-purple-500" },
              { label: "Audit Trail Coverage", value: 100, color: "bg-cyan-500" },
            ].map((m) => (
              <div key={m.label}>
                <div className="flex justify-between mb-1"><span className="text-[13px]">{m.label}</span><span className="text-[13px] font-bold">{m.value}%</span></div>
                <div className="progress-bar"><div className={`progress-bar-fill ${m.color}`} style={{ width: `${m.value}%` }} /></div>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Fraud Alerts by Type">
          <div className="space-y-2.5">
            {fraudTypes.length > 0 ? fraudTypes.map((f: {type: string, count: number, sev: string}) => (
              <div key={f.type} className="flex items-center justify-between py-1.5 border-b border-gray-50 last:border-0">
                <span className="text-[13px] text-[var(--text-primary)]">{f.type}</span>
                <div className="flex items-center gap-2">
                  <span className="text-[13px] font-bold">{f.count}</span>
                  <Badge status={f.sev} className="text-[11px]" />
                </div>
              </div>
            )) : (
              <p className="text-[13px] text-gray-500 py-4 text-center">No fraud alerts found</p>
            )}
          </div>
        </Card>

        <Card title="Recent Permission Changes">
          <div className="space-y-3">
            {permissionChanges.length > 0 ? permissionChanges.map((c: {user: string, change: string, by: string, time: string}, i: number) => (
              <div key={i} className="p-3 rounded-lg border border-[var(--border-color)]">
                <p className="text-[13px] font-semibold text-[var(--text-primary)]">{c.user}</p>
                <p className="text-[12px] text-gray-500 mt-0.5">{c.change}</p>
                <p className="text-[11px] text-gray-400 mt-1">By {c.by} · {c.time}</p>
              </div>
            )) : (
              <p className="text-[13px] text-gray-500 py-4 text-center border border-dashed rounded-lg">No recent changes</p>
            )}
          </div>
        </Card>
      </div>

      <Card title="Open Fraud Alerts" action={<Link href="/fraud"><Button variant="ghost" size="sm">View All</Button></Link>}>
        <Table columns={fraudColumns} data={fraudAlerts.slice(0, 5)} emptyMessage="No open fraud alerts" />
      </Card>

      <Card title="Recent Audit Events" action={<Link href="/audit"><Button variant="ghost" size="sm">View All</Button></Link>}>
        <Table columns={auditColumns} data={auditLogs.slice(0, 5)} emptyMessage="No recent audit events" />
      </Card>
    </div>
  );
}
