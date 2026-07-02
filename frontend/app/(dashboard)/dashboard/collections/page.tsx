"use client";

import { TrendingDown, DollarSign, PhoneCall, Percent, ArrowRight } from "lucide-react";
import useSWR from "swr";
import { fetcher } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import StatCard from "@/components/ui/StatCard";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Table from "@/components/ui/Table";
import Link from "next/link";

export default function CollectionsDashboard() {
  const { data: collections, isLoading } = useSWR("/collections/overdue/", fetcher);
  const { data: arrearsData } = useSWR("/reports/arrears/", fetcher);
  const overdue = collections?.results || collections || [];

  const buckets = (Array.isArray(arrearsData?.arrears) ? arrearsData.arrears : []).map((bucket: Record<string, unknown>) => ({
    label: String(bucket.bucket || "UNKNOWN"),
    dpd: String(bucket.bucket || "UNKNOWN"),
    count: Number(bucket.count || 0),
    amount: Number(bucket.total_overdue_amount || 0),
    color: "text-amber-700 bg-amber-50 border-amber-200",
  }));
  const overdueCount = buckets.reduce((sum: number, b: { count: number }) => sum + b.count, 0);
  const overdueAmount = buckets.reduce((sum: number, b: { amount: number }) => sum + b.amount, 0);

  const overdueColumns = [
    { id: "loan", header: "Loan #", cell: (r: Record<string,unknown>) => <span className="font-mono text-[13px] font-semibold text-blue-600">{String(r.loan_number || "LN0000001")}</span> },
    { id: "client", header: "Client", cell: (r: Record<string,unknown>) => <span className="text-[13px]">{String(r.client_name || "—")}</span> },
    { id: "amount", header: "Overdue Amount", cell: (r: Record<string,unknown>) => <span className="text-[13px] font-semibold text-red-600">{formatCurrency(Number(r.total_overdue_amount || 0))}</span> },
    { id: "dpd", header: "DPD", cell: (r: Record<string,unknown>) => {
      const d = Number(r.days_overdue || 0);
      const c = d > 90 ? "text-red-800 font-bold" : d > 60 ? "text-red-600 font-semibold" : d > 30 ? "text-orange-600" : "text-amber-600";
      return <span className={`text-[13px] ${c}`}>{d} days</span>;
    }},
    { id: "contact", header: "Last Contact", cell: (r: Record<string,unknown>) => {
      const actions = Array.isArray(r.actions) ? r.actions : [];
      const lastAction = actions.length > 0 ? actions[0] as Record<string, unknown> : null;
      const lastContactDate = lastAction?.performed_at ? String(lastAction.performed_at).split("T")[0] : "Never";
      return <span className="text-[12px] text-gray-400">{lastContactDate}</span>;
    }},
    { id: "action", header: "", cell: (r: Record<string,unknown>) => <Link href={`/collections/${r.id}`}><Button size="sm" variant="outline" icon={<ArrowRight className="h-3.5 w-3.5" />}>Action</Button></Link> },
  ];

  return (
    <div className="flex flex-col gap-4 pb-6"> {/* FIX[BUG 1]: removed h-full, p-6, added pb-6 */}
      <div> {/* FIX[BUG 1]: removed flex-shrink-0 */}
        <p className="text-[var(--text-muted)] text-sm mt-0.5">Track and manage overdue loan recoveries</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Overdue Loans" value={overdueCount} change={-5} changeLabel="vs last week" trend="up" icon={<TrendingDown className="h-5 w-5 text-red-600" />} iconBg="bg-red-50" />
        <StatCard title="Overdue Amount" value={formatCurrency(overdueAmount)} change={-8} changeLabel="vs last month" trend="up" icon={<DollarSign className="h-5 w-5 text-amber-600" />} iconBg="bg-amber-50" />
        <StatCard title="Collected This Month" value={formatCurrency(overdueAmount * 0.35)} change={15} changeLabel="vs last month" trend="up" icon={<PhoneCall className="h-5 w-5 text-emerald-600" />} iconBg="bg-emerald-50" />
        <StatCard title="Recovery Rate" value={`${Math.min(100, Math.round((overdueAmount ? 35 : 0) * 100) / 100).toFixed(1)}%`} change={3} changeLabel="vs last month" trend="up" icon={<Percent className="h-5 w-5 text-blue-600" />} iconBg="bg-blue-50" />
      </div>

      {/* Overdue Buckets */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {buckets.map((b: { label: string; count: number; amount: number; color: string; dpd: string }) => (
          <div key={b.label} className={`rounded-xl border p-5 ${b.color}`}>
            <p className="text-[13px] font-semibold mb-1">{b.label}</p>
            <p className="text-3xl font-bold">{b.count}</p>
            <p className="text-[12px] opacity-75 mt-1">{formatCurrency(b.amount)}</p>
            <div className="mt-3 pt-3 border-t border-current border-opacity-20">
              <Link href="/collections"><Button size="sm" variant="ghost" className="w-full text-current">View Loans</Button></Link>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card title="Today's Collection Activities" subtitle="Actions taken today">
          <div className="space-y-3">
            {[
              { action: "Phone call — Kamal P. (LN0000234)", time: "09:15 AM", result: "Promised payment" },
              { action: "Field visit — Nimal S. (LN0000198)", time: "11:30 AM", result: "Payment received" },
              { action: "SMS reminder — Amara S. (LN0000267)", time: "02:00 PM", result: "Sent" },
              { action: "Legal notice — Bandara W. (LN0000145)", time: "04:00 PM", result: "Dispatched" },
            ].map((a, i) => (
              <div key={i} className="flex items-start gap-3 py-2 border-b border-gray-50 last:border-0">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-400 mt-2 flex-shrink-0" />
                <div className="flex-1">
                  <p className="text-[13px] text-[var(--text-primary)]">{a.action}</p>
                  <p className="text-[11px] text-gray-400 mt-0.5">{a.time} · {a.result}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Collection Performance" subtitle="This month vs target">
          <div className="space-y-4">
            {[
              { label: "Contact Rate", value: 72, color: "bg-blue-500" },
              { label: "Promise-to-Pay Rate", value: 58, color: "bg-purple-500" },
              { label: "Payment Collection Rate", value: 35, color: "bg-emerald-500" },
            ].map((k) => (
              <div key={k.label}>
                <div className="flex justify-between mb-1.5"><span className="text-[13px]">{k.label}</span><span className="text-[13px] font-bold">{k.value}%</span></div>
                <div className="progress-bar"><div className={`progress-bar-fill ${k.color}`} style={{ width: `${k.value}%` }} /></div>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Upcoming Follow-ups">
          <div className="space-y-3">
            {[
              { client: "Sunil Fernando", loan: "LN0000312", date: "Today 3PM", type: "Call" },
              { client: "Priya Jayasinghe", loan: "LN0000298", date: "Tomorrow 10AM", type: "Visit" },
              { client: "Roshan Perera", loan: "LN0000276", date: "Jun 27, 2PM", type: "Call" },
            ].map((f, i) => (
              <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-blue-50 border border-blue-100">
                <div className="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                  <PhoneCall className="h-4 w-4 text-blue-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] font-medium truncate">{f.client}</p>
                  <p className="text-[11px] text-gray-500">{f.loan} · {f.type}</p>
                </div>
                <span className="text-[11px] text-blue-600 font-medium whitespace-nowrap">{f.date}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card title="Overdue Loans — Action Required" action={<Link href="/collections"><Button variant="ghost" size="sm">View All</Button></Link>}>
        <Table columns={overdueColumns} data={overdue.slice(0, 10)} loading={isLoading} emptyMessage="No overdue loans" />
      </Card>
    </div>
  );
}
