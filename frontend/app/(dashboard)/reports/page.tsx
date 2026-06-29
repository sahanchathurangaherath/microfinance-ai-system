"use client";

import { BarChart2, Download, Calendar, DollarSign, Users, FileText, TrendingUp, PieChart } from "lucide-react";
import Card from "@/components/ui/Card";
import StatCard from "@/components/ui/StatCard";
import Button from "@/components/ui/Button";
import { formatCurrency } from "@/lib/utils";

export default function ReportsPage() {
  const reports = [
    { title: "Portfolio Summary", desc: "Overall lending portfolio health and composition", icon: <PieChart className="h-6 w-6 text-blue-600" />, bg: "bg-blue-50" },
    { title: "Disbursement Report", desc: "Monthly disbursement volumes and trends", icon: <DollarSign className="h-6 w-6 text-emerald-600" />, bg: "bg-emerald-50" },
    { title: "Collection Report", desc: "Recovery rates and overdue loan tracking", icon: <TrendingUp className="h-6 w-6 text-purple-600" />, bg: "bg-purple-50" },
    { title: "Client Analytics", desc: "Client demographics and acquisition trends", icon: <Users className="h-6 w-6 text-cyan-600" />, bg: "bg-cyan-50" },
    { title: "Loan Pipeline", desc: "Application funnel and conversion rates", icon: <FileText className="h-6 w-6 text-amber-600" />, bg: "bg-amber-50" },
    { title: "Risk Distribution", desc: "Risk scoring breakdown across portfolio", icon: <BarChart2 className="h-6 w-6 text-red-600" />, bg: "bg-red-50" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-[var(--text-muted)] text-sm mt-0.5">Generate and view operational reports</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" icon={<Calendar className="h-4 w-4" />}>Date Range</Button>
          <Button variant="outline" size="sm" icon={<Download className="h-4 w-4" />}>Export All</Button>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard title="Total Portfolio (AUM)" value={formatCurrency(142000000)} change={12} trend="up" icon={<DollarSign className="h-5 w-5 text-blue-600" />} iconBg="bg-blue-50" />
        <StatCard title="Active Clients" value="1,847" change={8} trend="up" icon={<Users className="h-5 w-5 text-emerald-600" />} iconBg="bg-emerald-50" />
        <StatCard title="Avg Loan Size" value={formatCurrency(128000)} icon={<FileText className="h-5 w-5 text-purple-600" />} iconBg="bg-purple-50" />
        <StatCard title="NPL Ratio" value="2.8%" change={-0.3} trend="up" icon={<TrendingUp className="h-5 w-5 text-amber-600" />} iconBg="bg-amber-50" />
      </div>

      {/* Report Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {reports.map((r) => (
          <Card key={r.title} className="hover:border-blue-200 transition-all cursor-pointer group">
            <div className="flex items-start gap-4">
              <div className={`w-12 h-12 rounded-xl ${r.bg} flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform`}>
                {r.icon}
              </div>
              <div className="flex-1">
                <h3 className="text-[15px] font-semibold text-[var(--text-primary)] mb-1">{r.title}</h3>
                <p className="text-[13px] text-[var(--text-muted)] leading-relaxed">{r.desc}</p>
                <div className="flex gap-2 mt-3">
                  <Button size="sm" variant="outline" icon={<BarChart2 className="h-3.5 w-3.5" />}>View</Button>
                  <Button size="sm" variant="ghost" icon={<Download className="h-3.5 w-3.5" />}>Export</Button>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Sample Charts area */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <Card title="Monthly Disbursements" subtitle="Last 6 months">
          <div className="flex items-end gap-2 h-40">
            {[
              { month: "Jan", value: 4200000, pct: 60 },
              { month: "Feb", value: 3800000, pct: 54 },
              { month: "Mar", value: 5100000, pct: 73 },
              { month: "Apr", value: 4900000, pct: 70 },
              { month: "May", value: 6200000, pct: 88 },
              { month: "Jun", value: 7000000, pct: 100 },
            ].map((m) => (
              <div key={m.month} className="flex-1 flex flex-col items-center gap-1">
                <div className="w-full gradient-primary rounded-t-lg transition-all hover:opacity-80" style={{ height: `${m.pct}%` }} />
                <span className="text-[11px] text-gray-500">{m.month}</span>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Loan Purpose Distribution" subtitle="Current portfolio">
          <div className="space-y-2.5">
            {[
              { label: "Business Expansion", pct: 32, color: "bg-blue-500" },
              { label: "Working Capital", pct: 24, color: "bg-emerald-500" },
              { label: "Agriculture", pct: 18, color: "bg-amber-500" },
              { label: "Equipment Purchase", pct: 12, color: "bg-purple-500" },
              { label: "Education", pct: 8, color: "bg-cyan-500" },
              { label: "Other", pct: 6, color: "bg-gray-400" },
            ].map((l) => (
              <div key={l.label}>
                <div className="flex justify-between mb-0.5">
                  <span className="text-[13px] text-[var(--text-primary)]">{l.label}</span>
                  <span className="text-[13px] font-semibold">{l.pct}%</span>
                </div>
                <div className="progress-bar">
                  <div className={`progress-bar-fill ${l.color}`} style={{ width: `${l.pct}%` }} />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
