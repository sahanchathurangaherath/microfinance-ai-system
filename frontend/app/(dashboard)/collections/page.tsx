"use client";

import { useState } from "react";
import Link from "next/link";
import useSWR from "swr";
import { Search, ArrowRight } from "lucide-react";
import { fetcher } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import { TableSkeleton } from "@/components/ui/Skeleton";
import { usePermissions } from "@/lib/permissions";

export default function CollectionsPage() {
  const { can } = usePermissions();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const params = new URLSearchParams();
  if (search) params.set("search", search);
  params.set("page", String(page));

  const { data, isLoading } = useSWR(`/collections/overdue/?${params.toString()}`, fetcher);
  const collections = data?.results || data || [];
  const total = data?.count || collections.length;
  const totalPages = Math.ceil(total / 10);

  return (
    <div className="flex flex-col h-full gap-4">
      <div className="flex-shrink-0 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <p className="text-[var(--text-muted)] text-sm mt-0.5">{total} overdue loans in collection</p>
        </div>
      </div>

      <Card padding={false} className="flex-1 flex flex-col min-h-0">
        <div className="flex-shrink-0 flex flex-col gap-3 p-4 border-b border-[var(--border-color)] lg:flex-row lg:items-center">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-muted)]" />
            <input type="text" placeholder="Search by loan # or client name..." value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="w-full pl-9 pr-4 py-2 text-[13px] border border-[var(--border-color)] rounded-lg outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 bg-[var(--bg-primary)] text-[var(--text-primary)]" />
          </div>
          <p className="text-[13px] text-[var(--text-muted)] self-start lg:self-center lg:ml-2">Showing {collections.length} of {total}</p>
        </div>

        {isLoading ? <TableSkeleton rows={8} cols={6} /> : (
          <div className="flex-1 overflow-y-auto">
            <table className="w-full min-w-[860px] text-sm border-collapse">
              <thead className="sticky top-0 bg-[var(--bg-secondary)] z-10 border-b border-[var(--border-color)]">
                <tr>
                  <th className="text-left text-xs font-medium text-[var(--text-muted)] uppercase tracking-wide px-4 py-3">Loan #</th>
                  <th className="text-left text-xs font-medium text-[var(--text-muted)] uppercase tracking-wide px-4 py-3">Client</th>
                  <th className="text-left text-xs font-medium text-[var(--text-muted)] uppercase tracking-wide px-4 py-3">Overdue Amount</th>
                  <th className="text-left text-xs font-medium text-[var(--text-muted)] uppercase tracking-wide px-4 py-3">DPD</th>
                  <th className="text-left text-xs font-medium text-[var(--text-muted)] uppercase tracking-wide px-4 py-3">Last Contact</th>
                  <th className="text-left text-xs font-medium text-[var(--text-muted)] uppercase tracking-wide px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {collections.length === 0 ? (
                  <tr><td colSpan={6} className="text-center py-12 text-[var(--text-muted)]">No overdue loans found</td></tr>
                ) : collections.map((r: Record<string,unknown>) => {
                  const d = Number(r.days_past_due || 0);
                  const c = d > 90 ? "text-red-800 font-bold" : d > 60 ? "text-red-600 font-semibold" : d > 30 ? "text-orange-600" : "text-amber-600";
                  return (
                    <tr key={String(r.id)} className="border-b border-[var(--border-color)] hover:bg-[var(--bg-hover)] transition-colors">
                      <td className="px-4 py-3 text-sm"><span className="font-mono text-[13px] font-semibold text-blue-600">{String(r.loan_number || "LN0000001")}</span></td>
                      <td className="px-4 py-3 text-sm"><span className="text-[var(--text-primary)]">{String(r.client_name || "—")}</span></td>
                      <td className="px-4 py-3 text-sm"><span className="font-semibold text-red-600">{formatCurrency(Number(r.overdue_amount || 0))}</span></td>
                      <td className="px-4 py-3 text-sm"><span className={c}>{d} days</span></td>
                      <td className="px-4 py-3 text-sm"><span className="text-[var(--text-muted)]">{String(r.last_contact_date || "Never")}</span></td>
                      <td className="px-4 py-3 text-sm"><Link href={`/collections/${r.id}`}><Button size="sm" variant="outline" icon={<ArrowRight className="h-3.5 w-3.5" />}>Action</Button></Link></td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}

        {totalPages > 1 && (
          <div className="flex-shrink-0 flex items-center justify-between px-4 py-3 border-t border-[var(--border-color)] bg-[var(--bg-secondary)]">
            <Button variant="outline" size="sm" disabled={page === 1} onClick={() => setPage(p => p - 1)}>Previous</Button>
            <span className="text-[13px] text-[var(--text-muted)]">Page {page} of {totalPages}</span>
            <Button variant="outline" size="sm" disabled={page === totalPages} onClick={() => setPage(p => p + 1)}>Next</Button>
          </div>
        )}
      </Card>
    </div>
  );
}
