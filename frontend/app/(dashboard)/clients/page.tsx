"use client";

import { useState } from "react";
import Link from "next/link";
import useSWR from "swr";
import { Search, Plus, Eye, Filter } from "lucide-react";
import { fetcher } from "@/lib/api";
import { formatDate, getInitials, cn } from "@/lib/utils";
import Button from "@/components/ui/Button";
import Badge from "@/components/ui/Badge";
import Card from "@/components/ui/Card";
import { TableSkeleton } from "@/components/ui/Skeleton";
import EmptyState from "@/components/ui/EmptyState";
import ErrorState from "@/components/ui/ErrorState";
import { usePermissions } from "@/lib/permissions";

interface Client {
  id: number;
  client_number: string;
  first_name: string;
  last_name: string;
  nic_number: string;
  phone_primary: string;
  email: string;
  status: string;
  data_quality_score: number;
  created_at: string;
}

const STATUS_OPTIONS = [
  { value: "", label: "All Statuses" },
  { value: "PENDING", label: "Pending" },
  { value: "KYC_SUBMITTED", label: "KYC Submitted" },
  { value: "VERIFIED", label: "Verified" },
  { value: "ACTIVE", label: "Active" },
  { value: "REJECTED", label: "Rejected" },
  { value: "SUSPENDED", label: "Suspended" },
];

export default function ClientsPage() {
  const { can } = usePermissions();
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);

  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (status) params.set("status", status);
  params.set("page", String(page));

  const { data, error, isLoading, mutate } = useSWR(`/clients/?${params.toString()}`, fetcher);

  const clients: Client[] = data?.results || data || [];
  const total = data?.count || clients.length;
  const pageSize = 10;
  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="flex flex-col h-full gap-4">
      {/* Header */}
      <div className="flex-shrink-0 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <p className="text-[var(--text-muted)] text-sm mt-0.5">
            {total} total clients registered
          </p>
        </div>
        {can("clients:write") && (
          <Link href="/clients/new">
            <Button icon={<Plus className="h-4 w-4" />}>Register New Client</Button>
          </Link>
        )}
      </div>

      <Card padding={false} className="flex-1 flex flex-col min-h-0">
        {/* Filters */}
        <div className="flex-shrink-0 flex flex-col gap-3 p-4 border-b border-gray-200 lg:flex-row lg:items-center">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-muted)]" />
            <input
              type="text"
              placeholder="Search by name, NIC, phone..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="w-full pl-9 pr-4 py-2 text-[13px] border border-gray-300 rounded-lg outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-[var(--text-muted)]" />
            <select
              value={status}
              onChange={(e) => { setStatus(e.target.value); setPage(1); }}
              className="text-[13px] border border-gray-300 rounded-lg px-3 py-2 outline-none focus:border-blue-500 bg-white"
            >
              {STATUS_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <p className="text-sm text-gray-400 self-start lg:self-center lg:ml-2">
            Showing {clients.length} of {total}
          </p>
        </div>

        {/* Table */}
        {isLoading && !clients.length ? (
          <TableSkeleton rows={8} cols={7} />
        ) : error && !clients.length ? (
          <div className="flex-1 p-4 bg-white rounded-2xl border border-gray-200">
            <ErrorState 
              title="Failed to load clients" 
              message={typeof error === 'string' ? error : error?.message || "An error occurred while loading clients data."}
              onRetry={() => mutate()} 
            />
          </div>
        ) : clients.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full py-20 text-center gap-3">
            <EmptyState variant="no-data" description="No clients found matching your filters" />
            {can("clients:write") && (
              <Link href="/clients/new"><Button size="sm">Register First Client</Button></Link>
            )}
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto">
            <table className="w-full min-w-[780px] text-sm border-collapse">
              <thead className="sticky top-0 bg-white z-10 border-b border-gray-200">
                <tr>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wide px-4 py-3">Client #</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wide px-4 py-3">Full Name</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wide px-4 py-3">NIC Number</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wide px-4 py-3">Phone</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wide px-4 py-3">Status</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wide px-4 py-3">Data Quality</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wide px-4 py-3">Registered</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wide px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {clients.map((c) => (
                  <tr key={c.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 text-sm">
                      <span className="font-mono text-[13px] font-semibold text-blue-600">
                        {c.client_number}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <div className="flex items-center gap-2.5 min-w-0"> {/* FIX[BUG 15]: min-w-0 on flex parent */}
                        <div className="h-8 w-8 rounded-full flex items-center justify-center text-sm font-medium bg-blue-100 text-blue-700 flex-shrink-0">
                          {getInitials(c.first_name, c.last_name)}
                        </div>
                        <span className="text-[13px] font-medium truncate min-w-0"> {/* FIX[BUG 15]: truncate min-w-0 */}
                          {c.first_name} {c.last_name}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm"><span className="font-mono text-[13px]">{c.nic_number}</span></td>
                    <td className="px-4 py-3 text-sm"><span>{c.phone_primary}</span></td>
                    <td className="px-4 py-3 text-sm"><Badge status={c.status} /></td>
                    <td className="px-4 py-3 text-sm">
                      {c.data_quality_score != null ? (
                        <div className="flex items-center gap-2">
                          <div className="progress-bar w-16">
                            <div
                              className={`progress-bar-fill ${c.data_quality_score >= 80 ? "bg-emerald-500" : c.data_quality_score >= 60 ? "bg-amber-500" : "bg-red-500"}`}
                              style={{ width: `${c.data_quality_score}%` }}
                            />
                          </div>
                          <span className="text-[12px] font-medium text-[var(--text-secondary)]">
                            {c.data_quality_score.toFixed(1)}%
                          </span>
                        </div>
                      ) : <span className="text-[12px] text-gray-400">—</span>}
                    </td>
                    <td className="px-4 py-3 text-sm"><span className="text-gray-400">{formatDate(c.created_at)}</span></td>
                    <td className="px-4 py-3 text-sm">
                      <Link href={`/clients/${c.id}`}>
                        <Button size="sm" variant="ghost" icon={<Eye className="h-3.5 w-3.5" />}>View</Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex-shrink-0 flex items-center justify-between px-4 py-3 border-t border-gray-200">
            <Button
              variant="outline"
              size="sm"
              disabled={page === 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </Button>
            <div className="flex items-center gap-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const p = i + 1;
                return (
                  <button
                    key={p}
                    onClick={() => setPage(p)}
                    className={`w-8 h-8 rounded-lg text-[13px] font-medium transition-colors ${page === p ? "bg-blue-600 text-white" : "text-gray-600 hover:bg-gray-100"}`}
                  >
                    {p}
                  </button>
                );
              })}
            </div>
            <Button
              variant="outline"
              size="sm"
              disabled={page === totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            >
              Next
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
}
