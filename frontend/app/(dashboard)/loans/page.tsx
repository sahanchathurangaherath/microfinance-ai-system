"use client";

import { useState } from "react";
import Link from "next/link";
import useSWR from "swr";
import { Search, Plus, Eye, Filter } from "lucide-react";
import { fetcher } from "@/lib/api";
import { formatCurrency, formatDate, cn } from "@/lib/utils";
import Button from "@/components/ui/Button";
import Badge from "@/components/ui/Badge";
import Card from "@/components/ui/Card";
import { TableSkeleton } from "@/components/ui/Skeleton";
import { usePermissions } from "@/lib/permissions";

const STATUSES = ["", "DRAFT", "SUBMITTED", "AI_SCREENING", "RISK_REVIEWED", "MANAGER_REVIEW", "COMMITTEE_REVIEW", "APPROVED", "DISBURSED", "REJECTED"];

export default function LoansPage() {
  const { can } = usePermissions();
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);

  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (status) params.set("status", status);
  params.set("page", String(page));

  const { data, error, isLoading, mutate } = useSWR(`/loans/applications/?${params.toString()}`, fetcher);
  const loans = data?.results || data || [];
  const total = data?.count || loans.length;
  const totalPages = Math.ceil(total / 10);

  const pipelineCounts = loans.reduce((acc: Record<string, number>, loan: Record<string, unknown>) => {
    const s = String(loan.status || "DRAFT").toUpperCase();
    acc[s] = (acc[s] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="flex flex-col h-full gap-4">
      <div className="flex-shrink-0 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <p className="text-[var(--text-muted)] text-sm mt-0.5">{total} total applications</p>
        </div>
        {can("loans:write") && (
          <Link href="/loans/new"><Button icon={<Plus className="h-4 w-4" />}>New Application</Button></Link>
        )}
      </div>

      {/* Pipeline Visualization */}
      <div className="flex-shrink-0 flex gap-2 px-4 py-3 rounded-2xl border border-gray-200 bg-white/80 overflow-x-auto">
        {[
          { label: "Draft", key: "DRAFT", color: "bg-gray-100 text-gray-700" },
          { label: "Submitted", key: "SUBMITTED", color: "bg-amber-50 text-amber-700" },
          { label: "AI Review", key: "AI_SCREENING", color: "bg-blue-50 text-blue-700" },
          { label: "Risk", key: "RISK_REVIEWED", color: "bg-purple-50 text-purple-700" },
          { label: "Manager", key: "MANAGER_REVIEW", color: "bg-indigo-50 text-indigo-700" },
          { label: "Committee", key: "COMMITTEE_REVIEW", color: "bg-violet-50 text-violet-700" },
          { label: "Approved", key: "APPROVED", color: "bg-emerald-50 text-emerald-700" },
          { label: "Disbursed", key: "DISBURSED", color: "bg-green-50 text-green-700" },
          { label: "Rejected", key: "REJECTED", color: "bg-red-50 text-red-700" },
        ].map((s) => (
          <button
            key={s.key}
            onClick={() => { setStatus(status === s.key ? "" : s.key); setPage(1); }}
            className={cn(
              "flex flex-col items-center px-3 py-2 rounded-xl min-w-[74px] text-center border transition-colors shadow-sm",
              status === s.key ? "border-blue-500 font-semibold" : "border-transparent",
              s.color
            )}
          >
            <span className="text-lg font-bold">{pipelineCounts[s.key] || 0}</span>
            <span className="text-[10px] font-medium mt-0.5 whitespace-nowrap">{s.label}</span>
          </button>
        ))}
      </div>

      <Card padding={false} className="flex-1 flex flex-col min-h-0">
        {/* Filters */}
        <div className="flex-shrink-0 flex flex-col gap-3 p-4 border-b border-gray-200 lg:flex-row lg:items-center">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-muted)]" />
            <input type="text" placeholder="Search by app # or client name..." value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="w-full pl-9 pr-4 py-2 text-[13px] border border-gray-300 rounded-lg outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100" />
          </div>
          <div className="flex items-center gap-2 lg:ml-auto">
            <Filter className="h-4 w-4 text-[var(--text-muted)]" />
            <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}
              className="text-[13px] border border-gray-300 rounded-lg px-3 py-2 outline-none focus:border-blue-500 bg-white">
              {STATUSES.map((s) => <option key={s} value={s}>{s || "All Statuses"}</option>)}
            </select>
          </div>
          <p className="text-[13px] text-gray-400 self-start lg:self-center lg:ml-2">Showing {loans.length} of {total}</p>
        </div>

        {isLoading ? <TableSkeleton rows={8} cols={7} /> : (
          <div className="flex-1 overflow-y-auto">
            <table className="w-full min-w-[860px] text-sm border-collapse">
              <thead className="sticky top-0 bg-white z-10 border-b border-gray-200">
                <tr>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wide px-4 py-3">App #</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wide px-4 py-3">Client</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wide px-4 py-3">Amount (LKR)</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wide px-4 py-3">Product</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wide px-4 py-3">Duration</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wide px-4 py-3">Status</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wide px-4 py-3">Applied</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wide px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loans.length === 0 ? (
                  <tr><td colSpan={8} className="text-center py-12 text-[var(--text-muted)]">No loan applications found</td></tr>
                ) : loans.map((l: Record<string,unknown>) => (
                  <tr key={String(l.id)} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 text-sm"><span className="font-mono text-[13px] font-semibold text-blue-600">{String(l.application_number || "—")}</span></td>
                    <td className="px-4 py-3 text-sm"><span>{String((l.client as Record<string,unknown>)?.first_name || "—")} {String((l.client as Record<string,unknown>)?.last_name || "")}</span></td>
                    <td className="px-4 py-3 text-sm"><span>{formatCurrency(Number(l.requested_amount || 0))}</span></td>
                    <td className="px-4 py-3 text-sm"><span>{String((l.loan_product as Record<string,unknown>)?.name || "—")}</span></td>
                    <td className="px-4 py-3 text-sm"><span>{String(l.requested_duration_months || "—")} mo</span></td>
                    <td className="px-4 py-3 text-sm"><Badge status={String(l.status || "DRAFT")} /></td>
                    <td className="px-4 py-3 text-sm"><span className="text-gray-400">{formatDate(String(l.created_at || new Date()))}</span></td>
                    <td className="px-4 py-3 text-sm"><Link href={`/loans/${l.id}`}><Button size="sm" variant="ghost" icon={<Eye className="h-3.5 w-3.5" />}>View</Button></Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {totalPages > 1 && (
          <div className="flex-shrink-0 flex items-center justify-between px-4 py-3 border-t border-gray-200">
            <Button variant="outline" size="sm" disabled={page === 1} onClick={() => setPage(p => p - 1)}>Previous</Button>
            <span className="text-[13px] text-[var(--text-muted)]">Page {page} of {totalPages}</span>
            <Button variant="outline" size="sm" disabled={page === totalPages} onClick={() => setPage(p => p + 1)}>Next</Button>
          </div>
        )}
      </Card>
    </div>
  );
}
