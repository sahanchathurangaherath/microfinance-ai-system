"use client";

import { useState } from "react";
import Link from "next/link";
import useSWR from "swr";
import { CheckCircle, XCircle, Clock, ArrowRight, Filter } from "lucide-react";
import { fetcher } from "@/lib/api";
import { formatCurrency, formatDate, formatRelativeTime, normalizeArrayData } from "@/lib/utils";
import Button from "@/components/ui/Button";
import Badge from "@/components/ui/Badge";
import Card from "@/components/ui/Card";
import StatCard from "@/components/ui/StatCard";
import Table from "@/components/ui/Table";

export default function ApprovalsPage() {
  const [statusFilter, setStatusFilter] = useState("");
  const params = statusFilter ? `?status=${statusFilter}` : "";
  const { data, error, isLoading, mutate } = useSWR(`/approvals/pending${params}`, fetcher);
  const approvals = normalizeArrayData<Record<string, unknown>>(data);

  const columns = [
    { id: "app", header: "App #", cell: (r: Record<string,unknown>) => <span className="font-mono text-[13px] font-semibold text-blue-600">{String((r.application as Record<string,unknown>)?.application_number || r.application_number || "—")}</span> },
    { id: "client", header: "Client", cell: (r: Record<string,unknown>) => <span className="text-[13px]">{String((r.application as Record<string,unknown>)?.client_name || r.client_name || "—")}</span> },
    { id: "amount", header: "Amount", cell: (r: Record<string,unknown>) => <span className="text-[13px] font-medium">{formatCurrency(Number((r.application as Record<string,unknown>)?.requested_amount || r.requested_amount || 0))}</span> },
    { id: "level", header: "Level", cell: (r: Record<string,unknown>) => <Badge status={String(r.approval_level || r.current_level || "MANAGER_REVIEW")} /> },
    { id: "status", header: "Decision", cell: (r: Record<string,unknown>) => <Badge status={String(r.status || r.decision || "PENDING")} /> },
    { id: "assigned", header: "Assigned To", cell: (r: Record<string,unknown>) => <span className="text-[13px] text-gray-500">{String(r.assigned_to || r.reviewer_name || "—")}</span> },
    { id: "date", header: "Submitted", cell: (r: Record<string,unknown>) => <span className="text-[12px] text-gray-400">{formatRelativeTime(String(r.created_at || new Date()))}</span> },
    { id: "action", header: "", cell: (r: Record<string,unknown>) => <Link href={`/loans/${typeof r.application === 'number' ? r.application : ((r.application as Record<string,unknown>)?.id || r.application_id || r.id)}`} className="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"><ArrowRight className="h-3.5 w-3.5" />Review</Link> },
  ];

  const pendingCount = approvals.filter((a: Record<string,unknown>) => a.status === "PENDING" || !a.decision).length;
  const approvedCount = approvals.filter((a: Record<string,unknown>) => a.status === "APPROVED" || a.decision === "APPROVED").length;
  const rejectedCount = approvals.filter((a: Record<string,unknown>) => a.status === "REJECTED" || a.decision === "REJECTED").length;

  return (
    <div className="space-y-6">
      <div>
        <p className="text-[var(--text-muted)] text-sm mt-0.5">Review and approve/reject loan applications</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard title="Pending Review" value={pendingCount} loading={isLoading} icon={<Clock className="h-5 w-5 text-amber-600" />} iconBg="bg-amber-50" />
        <StatCard title="Approved Today" value={approvedCount} loading={isLoading} icon={<CheckCircle className="h-5 w-5 text-emerald-600" />} iconBg="bg-emerald-50" />
        <StatCard title="Rejected Today" value={rejectedCount} loading={isLoading} icon={<XCircle className="h-5 w-5 text-red-600" />} iconBg="bg-red-50" />
      </div>

      <Card padding={false}>
        <div className="flex items-center gap-3 p-4 border-b border-[var(--border-color)] overflow-hidden">
          <Filter className="h-4 w-4 text-[var(--text-muted)] flex-shrink-0" />
          <div className="flex gap-2 overflow-x-auto scrollbar-none pb-1 -mr-4 pr-4 sm:mr-0 sm:pr-0">
            {["", "PENDING", "APPROVED", "REJECTED", "ESCALATED"].map(s => (
              <button key={s} onClick={() => setStatusFilter(s)}
                className={`px-3 py-1.5 rounded-lg text-[12px] font-medium transition-all flex-shrink-0 ${statusFilter === s ? "bg-blue-100 text-blue-700" : "text-gray-500 hover:bg-gray-100"}`}>
                {s || "All"}
              </button>
            ))}
          </div>
        </div>
        <Table columns={columns} data={approvals} loading={isLoading} error={error} onRetry={() => mutate()} emptyMessage="No pending approvals found" />
      </Card>
    </div>
  );
}
