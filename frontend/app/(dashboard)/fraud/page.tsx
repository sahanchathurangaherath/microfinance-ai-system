"use client";

import useSWR from "swr";
import { AlertTriangle, Search, Filter, Shield, Eye, CheckCircle, ShieldAlert } from "lucide-react";
import { fetcher } from "@/lib/api";
import { formatDate, formatRelativeTime, normalizeArrayData } from "@/lib/utils";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Table from "@/components/ui/Table";
import StatCard from "@/components/ui/StatCard";
import { useState } from "react";
import api from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import { usePermissions } from "@/lib/permissions";

export default function FraudPage() {
  const { can } = usePermissions();
  const toast = useToast();
  const [statusFilter, setStatusFilter] = useState("");
  const [isTriggering, setIsTriggering] = useState(false);
  const params = statusFilter ? `?is_resolved=${statusFilter}` : "";
  const { data, error, isLoading, mutate } = useSWR(can("fraud:read") ? `/fraud/alerts/${params}` : null, fetcher);
  const alerts = normalizeArrayData<Record<string, unknown>>(data);

  if (!can("fraud:read")) {
    return (
      <Card className="flex flex-col items-center justify-center text-center py-16 max-w-md mx-auto">
        <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-950/30 flex items-center justify-center mb-3">
          <ShieldAlert className="h-6 w-6 text-red-600" />
        </div>
        <h3 className="text-lg font-bold text-[var(--text-primary)]">Access Denied</h3>
        <p className="text-[var(--text-muted)] text-sm mt-2">
          You do not have permission to view Fraud Alerts.
        </p>
      </Card>
    );
  }

  const columns = [
    { id: "type", header: "Flag Type", cell: (r: Record<string,unknown>) => <span className="text-[13px] font-medium">{String(r.alert_type || "UNKNOWN").replace(/_/g, " ")}</span> },
    { id: "client", header: "Client", cell: (r: Record<string,unknown>) => <span className="text-[13px]">{String(r.client_name || (r.client as Record<string,unknown>)?.first_name || "—")}</span> },
    { id: "app", header: "Application", cell: (r: Record<string,unknown>) => <span className="font-mono text-[13px] text-blue-600">{String(r.application || "—")}</span> },
    { id: "severity", header: "Severity", cell: (r: Record<string,unknown>) => <Badge status={String(r.severity || "MEDIUM")} /> },
    { id: "desc", header: "Details", cell: (r: Record<string,unknown>) => <span className="text-[13px] text-gray-600 truncate max-w-xs block">{String(r.ai_rationale || "—")}</span> },
    { id: "resolved", header: "Status", cell: (r: Record<string,unknown>) => <Badge status={r.is_resolved ? "ACTIVE" : "PENDING"}>{r.is_resolved ? "Resolved" : "Open"}</Badge> },
    { id: "date", header: "Flagged", cell: (r: Record<string,unknown>) => <span className="text-[12px] text-gray-400">{formatRelativeTime(String(r.triggered_at || new Date()))}</span> },
    { id: "action", header: "", cell: (r: Record<string,unknown>) => <Button size="sm" variant="ghost" icon={<Eye className="h-3.5 w-3.5" />}>Review</Button> },
  ];

  const openCount = alerts.filter((a: Record<string,unknown>) => !a.is_resolved).length;
  const criticalCount = alerts.filter((a: Record<string,unknown>) => String(a.severity || "").toUpperCase() === "CRITICAL").length;
  const resolvedCount = alerts.filter((a: Record<string,unknown>) => a.is_resolved).length;

  const handleTriggerA5 = async () => {
    try {
      setIsTriggering(true);
      await api.post("/fraud/check/");
      mutate();
      toast.success("AI Fraud Check (A5) completed successfully!");
    } catch (err: any) {
      toast.error("Failed to trigger A5: " + (err.response?.data?.error || err.message));
    } finally {
      setIsTriggering(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <p className="text-[var(--text-muted)] text-sm mt-0.5">Monitor and investigate flagged activities</p>
        </div>
        <Button onClick={handleTriggerA5} disabled={isTriggering}>
          {isTriggering ? "Running..." : "Run AI Fraud Check"}
        </Button>
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
