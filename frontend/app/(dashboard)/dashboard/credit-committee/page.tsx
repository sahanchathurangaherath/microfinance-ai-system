"use client";

import { Vote, CheckCircle, XCircle, Users, ArrowRight } from "lucide-react";
import useSWR from "swr";
import { fetcher } from "@/lib/api";
import { formatCurrency, formatDate, normalizeArrayData } from "@/lib/utils";
import StatCard from "@/components/ui/StatCard";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Table from "@/components/ui/Table";
import Link from "next/link";

export default function CreditCommitteeDashboard() {
  const { data: approvals, isLoading } = useSWR("/approvals/?status=PENDING_COMMITTEE", fetcher);
  const pending = normalizeArrayData<Record<string, unknown>>(approvals);

  const getVoteCount = (value: unknown, fallback: number) => {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  };

  const committeeColumns = [
    { id: "app", header: "App #", cell: (r: Record<string,unknown>) => <span className="font-mono text-[13px] font-semibold text-blue-600">{String((r.application as Record<string,unknown>)?.application_number || "LA0000001")}</span> },
    { id: "client", header: "Client", cell: (r: Record<string,unknown>) => <span className="text-[13px]">{String((r.application as Record<string,unknown>)?.client_name || "—")}</span> },
    { id: "amount", header: "Amount", cell: (r: Record<string,unknown>) => <span className="text-[13px] font-semibold">{formatCurrency(Number((r.application as Record<string,unknown>)?.requested_amount || 0))}</span> },
    { id: "for", header: "Votes For", cell: (r: Record<string,unknown>) => <span className="text-emerald-600 font-bold">{String(getVoteCount((r.committee_decision as Record<string,unknown>)?.vote_for, 0))}</span> },
    { id: "against", header: "Votes Against", cell: (r: Record<string,unknown>) => <span className="text-red-600 font-bold">{String(getVoteCount((r.committee_decision as Record<string,unknown>)?.vote_against, 0))}</span> },
    { id: "quorum", header: "Quorum", cell: (r: Record<string,unknown>) => {
      const reached = (r.committee_decision as Record<string,unknown>)?.quorum_reached;
      return <Badge status={reached ? "ACTIVE" : "PENDING"} />;
    }},
    { id: "action", header: "", cell: (r: Record<string,unknown>) => <Link href={`/approvals/${r.id}`}><Button size="sm" icon={<ArrowRight className="h-3.5 w-3.5" />}>Vote</Button></Link> },
  ];

  return (
    <div className="flex flex-col gap-4 pb-6"> {/* FIX[BUG 1]: removed h-full, p-6, added pb-6 */}
      <div> {/* FIX[BUG 1]: removed flex-shrink-0 */}
        <p className="text-[var(--text-muted)] text-sm mt-0.5">Review high-value loan applications requiring committee decision</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Pending Committee Vote" value={pending.length || 8} icon={<Vote className="h-5 w-5 text-purple-600" />} iconBg="bg-purple-50" trend="neutral" />
        <StatCard title="Approved by Committee" value={34} change={12} changeLabel="this month" trend="up" icon={<CheckCircle className="h-5 w-5 text-emerald-600" />} iconBg="bg-emerald-50" />
        <StatCard title="Rejected by Committee" value={6} icon={<XCircle className="h-5 w-5 text-red-600" />} iconBg="bg-red-50" trend="neutral" />
        <StatCard title="Avg Loan Amount" value={formatCurrency(850000)} icon={<Users className="h-5 w-5 text-blue-600" />} iconBg="bg-blue-50" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card title="Voting Progress" subtitle="Current open committee cases">
          <div className="space-y-4">
            {[
              { app: "LA0000892", for: 3, against: 1, total: 5 },
              { app: "LA0000901", for: 2, against: 2, total: 5 },
              { app: "LA0000912", for: 4, against: 0, total: 5 },
            ].map((c) => (
              <div key={c.app} className="p-3 rounded-xl border border-[var(--border-color)]">
                <div className="flex justify-between mb-2">
                  <span className="font-mono text-[13px] font-semibold text-blue-600">{c.app}</span>
                  <span className="text-[12px] text-gray-400">{c.for + c.against}/{c.total} voted</span>
                </div>
                <div className="flex gap-1 mb-1.5">
                  {Array.from({ length: c.total }).map((_, i) => (
                    <div key={i} className={`flex-1 h-2 rounded-full ${i < c.for ? "bg-emerald-500" : i < c.for + c.against ? "bg-red-500" : "bg-gray-200"}`} />
                  ))}
                </div>
                <div className="flex text-[12px] gap-3">
                  <span className="text-emerald-600 font-semibold">✓ {c.for} For</span>
                  <span className="text-red-600 font-semibold">✗ {c.against} Against</span>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Recent Decisions" subtitle="Last 30 days">
          <div className="space-y-3">
            {[
              { app: "LA0000845", decision: "APPROVED", date: "Jun 23, 2026", amount: 1500000 },
              { app: "LA0000832", decision: "REJECTED", date: "Jun 21, 2026", amount: 900000 },
              { app: "LA0000818", decision: "APPROVED", date: "Jun 19, 2026", amount: 2000000 },
              { app: "LA0000801", decision: "APPROVED", date: "Jun 15, 2026", amount: 750000 },
            ].map((d) => (
              <div key={d.app} className="flex items-center gap-3 py-2 border-b border-gray-50 last:border-0">
                <div>
                  <p className="text-[13px] font-semibold text-blue-600 font-mono">{d.app}</p>
                  <p className="text-[11px] text-gray-400">{formatCurrency(d.amount)} · {d.date}</p>
                </div>
                <Badge status={d.decision} className="ml-auto" />
              </div>
            ))}
          </div>
        </Card>

        <Card title="Committee Stats">
          <div className="space-y-4">
            {[
              { label: "Approval Rate", value: 85, color: "bg-emerald-500" },
              { label: "Unanimous Decisions", value: 60, color: "bg-blue-500" },
              { label: "Quorum Achievement", value: 95, color: "bg-purple-500" },
            ].map((s) => (
              <div key={s.label}>
                <div className="flex justify-between mb-1"><span className="text-[13px]">{s.label}</span><span className="text-[13px] font-bold">{s.value}%</span></div>
                <div className="progress-bar"><div className={`progress-bar-fill ${s.color}`} style={{ width: `${s.value}%` }} /></div>
              </div>
            ))}
            <div className="p-3 bg-amber-50 rounded-xl mt-3">
              <p className="text-[12px] text-amber-700 font-semibold">Committee Threshold</p>
              <p className="text-xl font-bold text-amber-800">LKR 500,000+</p>
              <p className="text-[11px] text-amber-600">Applications above this amount require committee approval</p>
            </div>
          </div>
        </Card>
      </div>

      <Card title="Applications Pending Committee Vote" action={<Link href="/approvals"><Button variant="ghost" size="sm">View All</Button></Link>}>
        <Table columns={committeeColumns} data={pending.slice(0, 10)} loading={isLoading} emptyMessage="No applications pending committee vote" />
      </Card>
    </div>
  );
}
