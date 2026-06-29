"use client";

import useSWR from "swr";
import { AlertTriangle, Search, Filter, Shield, Eye, CheckCircle } from "lucide-react";
import { fetcher } from "@/lib/api";
import { formatDate, formatRelativeTime } from "@/lib/utils";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Table from "@/components/ui/Table";
import StatCard from "@/components/ui/StatCard";
import { useState } from "react";

export default function FraudPage() {
  const [statusFilter, setStatusFilter] = useState("");
  const params = statusFilter ? `?is_resolved=${statusFilter}` : "";
  const { data, error, isLoading, mutate } = useSWR(`/fraud/${params}`, fetcher);
  const alerts = data?.results || data || [];

  const columns = [
    { id: "type", header: "Flag Type", cell: (r: Record<string,unknown>) => <span className="text-[13px] font-medium">{String(r.flag_type || "UNKNOWN").replace(/_/g, " ")}</span> },
    { id: "client", header: "Client", cell: (r: Record<string,unknown>) => <span className="text-[13px]">{String(r.client_name || (r.client as Record<string,unknown>)?.first_name || "—")}</span> },
    { id: "app", header: "Application", cell: (r: Record<string,unknown>) => <span className="font-mono text-[13px] text-blue-600">{String(r.application_number || "—")}</span> },
    { id: "severity", header: "Severity", cell: (r: Record<string,unknown>) => <Badge status={String(r.severity || "MEDIUM")} /> },
    { id: "desc", header: "Details", cell: (r: Record<string,unknown>) => <span className="text-[13px] text-gray-600 truncate max-w-xs block">{String(r.description || r.flag_description || "—")}</span> },
    { id: "resolved", header: "Status", cell: (r: Record<string,unknown>) => <Badge status={r.is_resolved ? "ACTIVE" : "PENDING"}>{r.is_resolved ? "Resolved" : "Open"}</Badge> },
    { id: "date", header: "Flagged", cell: (r: Record<string,unknown>) => <span className="text-[12px] text-gray-400">{formatRelativeTime(String(r.created_at || new Date()))}</span> },
    { id: "action", header: "", cell: () => <Button size="sm" variant="ghost" icon={<Eye className="h-3.5 w-3.5" />}>Review</Button> },
  ];

  const openCount = alerts.filter((a: Record<string,unknown>) => !a.is_resolved).length;
  const criticalCount = alerts.filter((a: Record<string,unknown>) => String(a.severity || "").toUpperCase() === "CRITICAL").length;
  const resolvedCount = alerts.filter((a: Record<string,unknown>) => a.is_resolved).length;

  return (
    <div className="space-y-6">
      <div>
        <p className="text-[var(--text-muted)] text-sm mt-0.5">Monitor and investigate flagged activities</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard title="Open Alerts" value={openCount} loading={isLoading} icon={<AlertTriangle className="h-5 w-5 text-red-600" />} iconBg="bg-red-50" />
        <StatCard title="Critical Alerts" value={criticalCount} loading={isLoading} icon={<Shield className="h-5 w-5 text-red-700" />} iconBg="bg-red-100" />
        <StatCard title="Resolved Alerts" value={resolvedCount} loading={isLoading} icon={<CheckCircle className="h-5 w-5 text-emerald-600" />} iconBg="bg-emerald-50" />
      </div>

      <Card padding={false}>
        <div className="flex items-center gap-3 p-4 border-b border-[var(--border-color)]">
          <Filter className="h-4 w-4 text-[var(--text-muted)]" />
          {[
            { key: "", label: "All" },
            { key: "false", label: "Open" },
            { key: "true", label: "Resolved" },
          ].map(s => (
            <button key={s.key} onClick={() => setStatusFilter(s.key)}
              className={`px-3 py-1.5 rounded-lg text-[12px] font-medium transition-all ${statusFilter === s.key ? "bg-blue-100 text-blue-700" : "text-gray-500 hover:bg-gray-100"}`}>
              {s.label}
            </button>
          ))}
        </div>
        <Table columns={columns} data={alerts} loading={isLoading} error={error} onRetry={() => mutate()} emptyMessage="No fraud alerts found" />
      </Card>
    </div>
  );
}
