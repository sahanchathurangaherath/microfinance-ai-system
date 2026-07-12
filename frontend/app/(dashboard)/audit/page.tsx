"use client";

import useSWR from "swr";
import { Shield, Search, Calendar, User, Filter, ShieldAlert } from "lucide-react";
import { fetcher } from "@/lib/api";
import { formatRelativeTime, normalizeArrayData } from "@/lib/utils";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Table from "@/components/ui/Table";
import { useState } from "react";
import { usePermissions } from "@/lib/permissions";

export default function AuditPage() {
  const { can } = usePermissions();
  const [actionFilter, setActionFilter] = useState("");
  const params = actionFilter ? `?action_type=${actionFilter}` : "";
  const { data, error, isLoading, mutate } = useSWR(can("audit:read") ? `/audit/logs/${params}` : null, fetcher);
  const logs = normalizeArrayData<Record<string, unknown>>(data);

  if (!can("audit:read")) {
    return (
      <Card className="flex flex-col items-center justify-center text-center py-16 max-w-md mx-auto">
        <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-950/30 flex items-center justify-center mb-3">
          <ShieldAlert className="h-6 w-6 text-red-600" />
        </div>
        <h3 className="text-lg font-bold text-[var(--text-primary)]">Access Denied</h3>
        <p className="text-[var(--text-muted)] text-sm mt-2">
          You do not have permission to view the Audit Trail.
        </p>
      </Card>
    );
  }

  const columns = [
    { id: "user", header: "User", cell: (r: Record<string,unknown>) => (
      <div className="flex items-center gap-2 min-w-0"> {/* FIX[BUG 15]: min-w-0 on flex parent */}
        <div className="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
          <User className="h-3.5 w-3.5 text-blue-600" />
        </div>
        <span className="text-[13px] font-medium truncate min-w-0">{String(r.user_name || r.username || r.user || "System")}</span> {/* FIX[BUG 15]: truncate min-w-0 */}
      </div>
    )},
    { id: "action", header: "Action", cell: (r: Record<string,unknown>) => <Badge status={String(r.action_type || "UNKNOWN")} /> },
    { id: "resource", header: "Resource", cell: (r: Record<string,unknown>) => <span className="text-[13px] text-gray-600">{String(r.content_type || r.resource || "—")}</span> },
    { id: "desc", header: "Description", cell: (r: Record<string,unknown>) => <span className="text-[13px] text-gray-600 truncate max-w-xs block">{String(r.description || r.details || "—")}</span> },
    { id: "ip", header: "IP Address", cell: (r: Record<string,unknown>) => <span className="font-mono text-[12px] text-gray-400">{String(r.ip_address || "—")}</span> },
    { id: "time", header: "Timestamp", cell: (r: Record<string,unknown>) => (
      <span className="text-[12px] text-gray-400">{formatRelativeTime(String(r.timestamp || r.created_at || new Date()))}</span>
    )},
  ];

  const ACTIONS = ["", "LOGIN", "LOGOUT", "CREATE", "UPDATE", "DELETE", "VIEW", "APPROVE", "REJECT", "EXPORT"];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[var(--text-muted)] text-sm mt-0.5">Complete system activity log for compliance</p>
        </div>
        <div className="flex items-center gap-2 text-[12px] text-[var(--text-muted)]">
          <Shield className="h-4 w-4" />
          All actions are immutably logged
        </div>
      </div>

      <Card padding={false}>
        <div className="flex flex-wrap items-center gap-2 p-4 border-b border-[var(--border-color)]">
          <Filter className="h-4 w-4 text-[var(--text-muted)]" />
          {ACTIONS.map(a => (
            <button key={a} onClick={() => setActionFilter(a)}
              className={`px-3 py-1.5 rounded-lg text-[12px] font-medium transition-all ${actionFilter === a ? "bg-blue-100 text-blue-700" : "text-gray-500 hover:bg-gray-100"}`}>
              {a || "All"}
            </button>
          ))}
        </div>
        <Table columns={columns} data={logs} loading={isLoading} error={error} onRetry={() => mutate()} emptyMessage="No audit records found" />
      </Card>
    </div>
  );
}
