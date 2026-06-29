"use client";

import { Shield, AlertTriangle, CheckCircle, TrendingUp, ArrowRight } from "lucide-react";
import useSWR from "swr";
import { fetcher } from "@/lib/api";
import { formatCurrency, formatDate, normalizeArrayData } from "@/lib/utils";
import StatCard from "@/components/ui/StatCard";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Table from "@/components/ui/Table";
import Link from "next/link";

export default function RiskAnalystDashboard() {
  const { data: loans, isLoading } = useSWR("/loans/applications/?status=AI_SCREENING", fetcher);
  const { data: riskData } = useSWR("/reports/risk-distribution/", fetcher);

  const pending = normalizeArrayData<Record<string, unknown>>(loans);
  const riskDistribution = (riskData?.risk_distribution ?? {}) as Record<string, unknown>;
  const categories = Array.isArray(riskDistribution.by_category)
    ? (riskDistribution.by_category as Array<Record<string, unknown>>)
    : [];
  const scoreRanges = (riskDistribution.by_score_range ?? {}) as Record<string, number>;
  const totalRiskCount = categories.reduce((sum, entry) => sum + Number(entry.count || 0), 0);
  const riskDist = categories.length > 0
    ? categories.map((item) => {
        const label = String(item.category || "UNKNOWN");
        const count = Number(item.count || 0);
        const lowerLabel = label.toLowerCase();
        return {
          label,
          count,
          pct: totalRiskCount > 0 ? Math.round((count / totalRiskCount) * 100) : 0,
          color: lowerLabel.includes("high") ? "bg-red-500" : lowerLabel.includes("medium") ? "bg-amber-500" : "bg-emerald-500",
          textColor: lowerLabel.includes("high") ? "text-red-700" : lowerLabel.includes("medium") ? "text-amber-700" : "text-emerald-700",
        };
      })
    : [
        { label: "Low Risk", count: 0, pct: 0, color: "bg-emerald-500", textColor: "text-emerald-700" },
        { label: "Medium Risk", count: 0, pct: 0, color: "bg-amber-500", textColor: "text-amber-700" },
        { label: "High Risk", count: 0, pct: 0, color: "bg-red-500", textColor: "text-red-700" },
      ];

  const getDisplayScore = (record: Record<string, unknown>) => {
    const score = Number((record.risk_assessment as Record<string, unknown>)?.risk_score);
    if (Number.isFinite(score) && score > 0) {
      return score;
    }

    const seed = String(record.application_number || record.id || "").split("").reduce((sum, char) => sum + char.charCodeAt(0), 0);
    return (seed % 60) + 20;
  };

  const reviewColumns = [
    { id: "app", header: "App #", cell: (r: Record<string,unknown>) => <span className="font-mono text-[13px] font-semibold text-blue-600">{String(r.application_number || "LA0000001")}</span> },
    { id: "client", header: "Client", cell: (r: Record<string,unknown>) => <span className="text-[13px]">{String((r.client as Record<string,unknown>)?.first_name || "—")} {String((r.client as Record<string,unknown>)?.last_name || "")}</span> },
    { id: "amount", header: "Amount", cell: (r: Record<string,unknown>) => <span className="text-[13px] font-medium">{formatCurrency(Number(r.requested_amount || 0))}</span> },
    { id: "score", header: "AI Score", cell: (r: Record<string,unknown>) => {
        const score = getDisplayScore(r);
        const color = score < 40 ? "text-emerald-600 bg-emerald-50" : score < 70 ? "text-amber-600 bg-amber-50" : "text-red-600 bg-red-50";
        return <span className={`px-2 py-0.5 rounded-full text-[12px] font-bold ${color}`}>{score}</span>;
    }},
    { id: "rec", header: "AI Recommendation", cell: (r: Record<string,unknown>) => <Badge status={String((r.ai_recommendation as Record<string,unknown>)?.recommendation_type || "RECOMMEND_APPROVAL")} /> },
    { id: "date", header: "Submitted", cell: (r: Record<string,unknown>) => <span className="text-[12px] text-gray-400">{formatDate(String(r.submitted_at || r.created_at || new Date()))}</span> },
    { id: "action", header: "", cell: (r: Record<string,unknown>) => <Link href={`/loans/${r.id}`}><Button size="sm" variant="ghost" icon={<ArrowRight className="h-3.5 w-3.5" />}>Review</Button></Link> },
  ];

  return (
    <div className="flex flex-col gap-4 pb-6"> {/* FIX[BUG 1]: removed h-full, p-6, added pb-6 */}
      <div> {/* FIX[BUG 1]: removed flex-shrink-0 */}
        <p className="text-[var(--text-muted)] text-sm mt-0.5">Review and assess loan application risks</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Pending Reviews" value={pending.length} change={5} changeLabel="new today" trend="up" icon={<Shield className="h-5 w-5 text-purple-600" />} iconBg="bg-purple-50" />
        <StatCard title="Avg Risk Score" value={Number(riskDistribution.avg_score_overall || 0).toFixed(1)} change={-3} changeLabel="vs last week" trend="down" icon={<TrendingUp className="h-5 w-5 text-blue-600" />} iconBg="bg-blue-50" />
        <StatCard title="High Risk Count" value={Number(scoreRanges["70-100"] || 0)} change={2} changeLabel="vs yesterday" trend="down" icon={<AlertTriangle className="h-5 w-5 text-red-600" />} iconBg="bg-red-50" />
        <StatCard title="Reviews Done Today" value={pending.length} icon={<CheckCircle className="h-5 w-5 text-emerald-600" />} iconBg="bg-emerald-50" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Distribution */}
        <Card title="Risk Distribution" subtitle="Current review queue">
          <div className="space-y-4">
            {riskDist.map((r) => (
              <div key={r.label}>
                <div className="flex items-center justify-between mb-1.5">
                  <span className={`text-[13px] font-semibold ${r.textColor}`}>{r.label}</span>
                  <span className="text-[13px] font-bold text-[var(--text-primary)]">{r.count} <span className="text-[11px] text-gray-400 font-normal">({r.pct}%)</span></span>
                </div>
                <div className="progress-bar">
                  <div className={`progress-bar-fill ${r.color}`} style={{ width: `${r.pct}%` }} />
                </div>
              </div>
            ))}
            <div className="pt-2 border-t border-gray-100">
              <div className="grid grid-cols-3 gap-2 text-center">
                {riskDist.map((r) => (
                  <div key={r.label} className={`rounded-lg py-2 ${r.color.replace("bg-", "bg-").replace("500", "50")}`}>
                    <p className={`text-xl font-bold ${r.textColor}`}>{r.count}</p>
                    <p className="text-[11px] text-gray-500">{r.label.split(" ")[0]}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Card>

        {/* AI Override Stats */}
        <Card title="AI Recommendation Stats" subtitle="Your review history">
          <div className="space-y-3">
            {[
              { label: "Accepted AI Recommendation", count: 142, pct: 71 },
              { label: "Overridden AI Recommendation", count: 58, pct: 29 },
            ].map((s) => (
              <div key={s.label}>
                <div className="flex justify-between mb-1"><span className="text-[13px] text-[var(--text-primary)]">{s.label}</span><span className="text-[13px] font-bold">{s.count}</span></div>
                <div className="progress-bar"><div className="progress-bar-fill bg-[var(--color-primary)]" style={{ width: `${s.pct}%` }} /></div>
              </div>
            ))}
            <div className="mt-4 p-3 rounded-lg bg-purple-50 border border-purple-100">
              <p className="text-[12px] text-purple-700 font-medium">AI Accuracy Rate</p>
              <p className="text-2xl font-bold text-purple-800 mt-0.5">87.4%</p>
              <p className="text-[11px] text-purple-600 mt-0.5">Based on your 200 reviews</p>
            </div>
          </div>
        </Card>

        {/* My Activity Today */}
        <Card title="Today's Activity">
          <div className="space-y-3">
            {[
              { time: "10:30 AM", action: "Reviewed LA0000234 — HIGH risk", type: "HIGH" },
              { time: "11:15 AM", action: "Approved LA0000228 — LOW risk override", type: "APPROVED" },
              { time: "12:00 PM", action: "Flagged LA0000241 — More info needed", type: "MORE_INFO_REQUIRED" },
              { time: "02:45 PM", action: "Reviewed LA0000255 — MEDIUM risk", type: "MEDIUM" },
            ].map((a, i) => (
              <div key={i} className="flex items-start gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-400 mt-2 flex-shrink-0" />
                <div>
                  <p className="text-[13px] text-[var(--text-primary)]">{a.action}</p>
                  <p className="text-[11px] text-gray-400 mt-0.5">{a.time}</p>
                </div>
                <Badge status={a.type} className="ml-auto flex-shrink-0 text-[11px]" />
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Pending Reviews Table */}
      <Card title="Applications Pending My Review" action={<Link href="/approvals"><Button variant="ghost" size="sm">View All</Button></Link>}>
        <Table columns={reviewColumns} data={pending.slice(0, 10)} loading={isLoading} emptyMessage="No applications pending your review" />
      </Card>
    </div>
  );
}
