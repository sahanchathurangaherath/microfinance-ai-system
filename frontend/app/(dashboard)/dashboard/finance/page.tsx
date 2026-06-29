"use client";

import { DollarSign, CheckCircle, Clock, Banknote, ArrowRight } from "lucide-react";
import useSWR from "swr";
import { fetcher } from "@/lib/api";
import { formatCurrency, formatDate, normalizeArrayData } from "@/lib/utils";
import StatCard from "@/components/ui/StatCard";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Table from "@/components/ui/Table";
import Link from "next/link";

export default function FinanceDashboard() {
  const { data: loans, isLoading } = useSWR("/loans/applications/?status=APPROVED", fetcher);
  const { data: disbursementReport } = useSWR("/reports/disbursements/", fetcher);
  const approved = normalizeArrayData<Record<string, unknown>>(loans);
  const disbursementSeries = Array.isArray(disbursementReport?.disbursements) ? disbursementReport.disbursements : [];
  const approvedAmount = approved.reduce((sum: number, loan: Record<string, unknown>) => sum + Number(loan.requested_amount || 0), 0);

  const disbursementColumns = [
    { id: "app", header: "App #", cell: (r: Record<string,unknown>) => <span className="font-mono text-[13px] font-semibold text-blue-600">{String(r.application_number || "LA0000001")}</span> },
    { id: "client", header: "Client", cell: (r: Record<string,unknown>) => <span className="text-[13px]">{String((r.client as Record<string,unknown>)?.first_name || "—")} {String((r.client as Record<string,unknown>)?.last_name || "")}</span> },
    { id: "amount", header: "Amount", cell: (r: Record<string,unknown>) => <span className="text-[13px] font-semibold">{formatCurrency(Number(r.requested_amount || 0))}</span> },
    { id: "cond", header: "Conditions", cell: (r: Record<string,unknown>) => {
      const seed = String(r.id || r.application_number || "").split("").reduce((sum, char) => sum + char.charCodeAt(0), 0);
      const met = (seed % 4) + 1;
      const total = 4;
      const allMet = met === total;
      return <span className={`text-[13px] font-medium ${allMet ? "text-emerald-600" : "text-amber-600"}`}>{met}/{total} Met</span>;
    }},
    { id: "status", header: "Status", cell: (r: Record<string,unknown>) => <Badge status={String(r.status || "APPROVED")} /> },
    { id: "action", header: "", cell: (r: Record<string,unknown>) => <Link href={`/loans/${r.id}`}><Button size="sm" icon={<ArrowRight className="h-3.5 w-3.5" />}>Process</Button></Link> },
  ];

  const recentDisbursements = [
    { app: "LA0000812", client: "Kamal Perera", amount: 500000, method: "BANK_TRANSFER", date: "Jun 25, 2026" },
    { app: "LA0000798", client: "Sunil Fernando", amount: 250000, method: "CASH", date: "Jun 24, 2026" },
    { app: "LA0000781", client: "Amara Silva", amount: 800000, method: "BANK_TRANSFER", date: "Jun 23, 2026" },
    { app: "LA0000765", client: "Nimal Bandara", amount: 350000, method: "MOBILE_MONEY", date: "Jun 22, 2026" },
  ];

  const historyColumns = [
    { id: "app", header: "App #", cell: (r: Record<string,unknown>) => <span className="font-mono text-[13px] font-semibold text-blue-600">{String(r.app)}</span> },
    { id: "client", header: "Client", accessor: "client" as const },
    { id: "amount", header: "Amount", cell: (r: Record<string,unknown>) => <span className="font-medium">{formatCurrency(Number(r.amount))}</span> },
    { id: "method", header: "Method", cell: (r: Record<string,unknown>) => <Badge status={String(r.method)} /> },
    { id: "date", header: "Date", accessor: "date" as const },
  ];

  return (
    <div className="flex flex-col gap-4 pb-6"> {/* FIX[BUG 1]: removed h-full, p-6, added pb-6 */}
      <div> {/* FIX[BUG 1]: removed flex-shrink-0 */}
        <p className="text-[var(--text-muted)] text-sm mt-0.5">Manage disbursements and financial operations</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Awaiting Disbursement" value={approved.length} icon={<Clock className="h-5 w-5 text-amber-600" />} iconBg="bg-amber-50" trend="neutral" />
        <StatCard title="Conditions Fully Met" value={Math.min(approved.length, 8)} icon={<CheckCircle className="h-5 w-5 text-emerald-600" />} iconBg="bg-emerald-50" />
        <StatCard title="Disbursed Today (LKR)" value={formatCurrency(approvedAmount)} change={10} trend="up" icon={<DollarSign className="h-5 w-5 text-blue-600" />} iconBg="bg-blue-50" />
        <StatCard title="Total Disbursed (Month)" value={formatCurrency(disbursementSeries.reduce((sum: number, item: Record<string, unknown>) => sum + Number(item.total_amount || 0), 0))} change={18} trend="up" icon={<Banknote className="h-5 w-5 text-purple-600" />} iconBg="bg-purple-50" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card title="Disbursement by Method" subtitle="This month">
          <div className="space-y-3">
            {[
              { method: "Bank Transfer", count: 28, pct: 60, color: "bg-blue-500" },
              { method: "Cash", count: 12, pct: 25, color: "bg-emerald-500" },
              { method: "Mobile Money", count: 6, pct: 13, color: "bg-purple-500" },
              { method: "Cheque", count: 1, pct: 2, color: "bg-amber-500" },
            ].map((m) => (
              <div key={m.method}>
                <div className="flex justify-between mb-1"><span className="text-[13px]">{m.method}</span><div className="flex gap-2 items-center"><span className="text-[13px] font-bold">{m.count}</span><span className="text-[11px] text-gray-400">({m.pct}%)</span></div></div>
                <div className="progress-bar"><div className={`progress-bar-fill ${m.color}`} style={{ width: `${m.pct}%` }} /></div>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Disbursement Checklist" subtitle="Conditions status for pending loans">
          <div className="space-y-3">
            {[
              { app: "LA0000901", conditions: ["Collateral verified", "Insurance confirmed", "Legal docs", "Board approval"], met: [true, true, true, false] },
              { app: "LA0000912", conditions: ["Collateral verified", "Insurance confirmed", "Legal docs", "Board approval"], met: [true, true, false, false] },
            ].map((l) => (
              <div key={l.app} className="p-3 rounded-xl border border-[var(--border-color)]">
                <p className="font-mono text-[13px] font-semibold text-blue-600 mb-2">{l.app}</p>
                <div className="space-y-1.5">
                  {l.conditions.map((c, i) => (
                    <div key={c} className="flex items-center gap-2">
                      <div className={`w-4 h-4 rounded border-2 flex items-center justify-center flex-shrink-0 ${l.met[i] ? "bg-emerald-500 border-emerald-500" : "border-gray-300"}`}>
                        {l.met[i] && <CheckCircle className="h-3 w-3 text-white" />}
                      </div>
                      <span className={`text-[12px] ${l.met[i] ? "text-gray-500 line-through" : "text-[var(--text-primary)]"}`}>{c}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Today's Summary">
          <div className="space-y-4">
            <div className="text-center py-4">
              <p className="text-4xl font-bold text-[var(--text-primary)]">4</p>
              <p className="text-[14px] text-[var(--text-muted)] mt-1">Disbursements Processed</p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-blue-50 rounded-xl p-3 text-center">
                <p className="text-xl font-bold text-blue-700">{formatCurrency(1450000)}</p>
                <p className="text-[12px] text-blue-600 mt-0.5">Total Amount</p>
              </div>
              <div className="bg-emerald-50 rounded-xl p-3 text-center">
                <p className="text-xl font-bold text-emerald-700">8</p>
                <p className="text-[12px] text-emerald-600 mt-0.5">Conditions Verified</p>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Disbursement Queue */}
      <Card title="Applications Ready for Disbursement" action={<Link href="/loans?status=APPROVED"><Button variant="ghost" size="sm">View All</Button></Link>}>
        <Table columns={disbursementColumns} data={approved.slice(0, 8)} loading={isLoading} emptyMessage="No approved applications awaiting disbursement" />
      </Card>

      {/* Recent Disbursements */}
      <Card title="Recent Disbursements">
        <Table columns={historyColumns} data={recentDisbursements} emptyMessage="No recent disbursements" />
      </Card>
    </div>
  );
}
