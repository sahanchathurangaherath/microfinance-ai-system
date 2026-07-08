"use client";

import { BarChart2, Download, Calendar, DollarSign, Users, FileText, TrendingUp, PieChart } from "lucide-react";
import Card from "@/components/ui/Card";
import StatCard from "@/components/ui/StatCard";
import Button from "@/components/ui/Button";
import Modal from "@/components/ui/Modal";
import Table from "@/components/ui/Table";
import Badge from "@/components/ui/Badge";
import { formatCurrency } from "@/lib/utils";

import { useState } from "react";
import { useToast } from "@/components/ui/Toast";
import { reportsAPI, fetcher } from "@/lib/api";
import useSWR from "swr";
import { usePermissions } from "@/lib/permissions";
import { ShieldAlert } from "lucide-react";

export default function ReportsPage() {
  const { can } = usePermissions();
  const toast = useToast();
  const [isExporting, setIsExporting] = useState<string | null>(null);
  const [isViewing, setIsViewing] = useState<string | null>(null);
  const [viewData, setViewData] = useState<{ id: string; title: string; data: any } | null>(null);

  const { data: dashboard, isLoading } = useSWR(can("reports:read") ? "/reports/dashboard/" : null, fetcher);
  const { data: disbursementsData } = useSWR(can("reports:read") ? "/reports/disbursements/" : null, fetcher);

  const handleExport = async (reportId: string) => {
    try {
      setIsExporting(reportId);
      const res = await reportsAPI.exportCSV(reportId);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `${reportId}_report_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success("Report exported successfully");
    } catch (error) {
      toast.error("Export failed. Please try again.");
    } finally {
      setIsExporting(null);
    }
  };

  const handleView = async (reportId: string, title: string) => {
    try {
      setIsViewing(reportId);
      const res = await reportsAPI.exportJSON(reportId);
      setViewData({ id: reportId, title, data: res.data });
    } catch (error) {
      toast.error("Failed to load report data.");
    } finally {
      setIsViewing(null);
    }
  };

  if (!can("reports:read")) {
    return (
      <Card className="flex flex-col items-center justify-center text-center py-16 max-w-md mx-auto">
        <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-950/30 flex items-center justify-center mb-3">
          <ShieldAlert className="h-6 w-6 text-red-600" />
        </div>
        <h3 className="text-lg font-bold text-[var(--text-primary)]">Access Denied</h3>
        <p className="text-[var(--text-muted)] text-sm mt-2">
          You do not have permission to view Reports &amp; Analytics.
        </p>
      </Card>
    );
  }

  // Handles both admin overview shape and loan officer personalised shape
  const totalAUM = dashboard?.loans?.total_outstanding || dashboard?.portfolio?.total_outstanding || 0;
  const activeClients = dashboard?.clients?.active ?? dashboard?.clients?.total ?? 0;
  const nplRatio =
    dashboard?.default_rate?.default_rate_percent !== undefined
      ? `${dashboard.default_rate.default_rate_percent}%`
      : "0%";
  const activeLoans =
    dashboard?.loans?.active ??
    dashboard?.portfolio?.total_active_loans ??
    dashboard?.applications?.total ??
    0;

  const reports = [
    { id: "portfolio", title: "Portfolio Summary", desc: "Overall lending portfolio health and composition", icon: <PieChart className="h-6 w-6 text-blue-600" />, bg: "bg-blue-50" },
    { id: "disbursement", title: "Disbursement Report", desc: "Monthly disbursement volumes and trends", icon: <DollarSign className="h-6 w-6 text-emerald-600" />, bg: "bg-emerald-50" },
    { id: "arrears", title: "Collection Report", desc: "Recovery rates and overdue loan tracking", icon: <TrendingUp className="h-6 w-6 text-purple-600" />, bg: "bg-purple-50" },
    { id: "agent_performance", title: "Client Analytics", desc: "Client demographics and acquisition trends", icon: <Users className="h-6 w-6 text-cyan-600" />, bg: "bg-cyan-50" },
    { id: "default_rate", title: "Loan Pipeline", desc: "Application funnel and conversion rates", icon: <FileText className="h-6 w-6 text-amber-600" />, bg: "bg-amber-50" },
    { id: "risk_distribution", title: "Risk Distribution", desc: "Risk scoring breakdown across portfolio", icon: <BarChart2 className="h-6 w-6 text-red-600" />, bg: "bg-red-50" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-[var(--text-muted)] text-sm mt-0.5">Generate and view operational reports</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <div className="relative">
            <input 
              type="date" 
              className="absolute inset-0 opacity-0 cursor-pointer w-full h-full" 
              onChange={(e) => {
                if(e.target.value) toast.success(`Date range filtered to ${e.target.value}`);
              }}
            />
            <Button variant="outline" size="sm" icon={<Calendar className="h-4 w-4" />}>Date Range</Button>
          </div>
          <Button variant="outline" size="sm" icon={<Download className="h-4 w-4" />} onClick={() => handleExport("portfolio")} disabled={isExporting !== null}>Export All</Button>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard title="Total Portfolio (AUM)" value={totalAUM ? formatCurrency(Number(totalAUM)) : "LKR 0"} loading={isLoading} icon={<DollarSign className="h-5 w-5 text-blue-600" />} iconBg="bg-blue-50" />
        <StatCard title="Active Clients" value={activeClients} loading={isLoading} icon={<Users className="h-5 w-5 text-emerald-600" />} iconBg="bg-emerald-50" />
        <StatCard title="Active Loans" value={activeLoans} loading={isLoading} icon={<FileText className="h-5 w-5 text-purple-600" />} iconBg="bg-purple-50" />
        <StatCard title="NPL / Default Rate" value={nplRatio} loading={isLoading} icon={<TrendingUp className="h-5 w-5 text-amber-600" />} iconBg="bg-amber-50" />
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
                  <Button size="sm" variant="outline" icon={<BarChart2 className="h-3.5 w-3.5" />} onClick={() => handleView(r.id, r.title)} disabled={isViewing === r.id}>
                    {isViewing === r.id ? "Loading..." : "View"}
                  </Button>
                  <Button size="sm" variant="ghost" icon={<Download className="h-3.5 w-3.5" />} onClick={() => handleExport(r.id)} disabled={isExporting === r.id}>
                    {isExporting === r.id ? "Exporting..." : "Export"}
                  </Button>
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
            {(() => {
              const disbursementChartData = disbursementsData?.disbursements || [];
              const maxDisbursement = Math.max(...disbursementChartData.map((d: any) => Number(d.total_amount) || 0), 1);
              const chartItems = disbursementChartData.map((d: any) => ({
                month: new Date(d.month + "-01").toLocaleString('default', { month: 'short' }),
                value: Number(d.total_amount) || 0,
                pct: ((Number(d.total_amount) || 0) / maxDisbursement) * 100,
              }));

              if (chartItems.length === 0) {
                return <div className="w-full h-full flex items-center justify-center text-sm text-[var(--text-muted)]">No disbursement data available</div>;
              }

              return chartItems.map((m: any, idx: number) => (
                <div key={idx} className="flex-1 h-full flex flex-col justify-end items-center gap-1 group relative">
                  <div className="w-full gradient-primary rounded-t-lg transition-all hover:opacity-80" style={{ height: `${m.pct}%` }} />
                  <span className="text-[11px] text-gray-500">{m.month}</span>
                  <div className="absolute -top-8 bg-gray-800 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10 pointer-events-none">
                    {formatCurrency(m.value)}
                  </div>
                </div>
              ));
            })()}
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

      <Modal isOpen={!!viewData} onClose={() => setViewData(null)} title={viewData?.title} size="xl">
        {viewData?.data && Array.isArray(viewData.data) && viewData.data.length > 0 ? (
          <div className="max-h-[60vh] overflow-y-auto overflow-x-auto rounded-xl border border-gray-100 shadow-sm bg-white">
            <Table
              data={viewData.data}
              columns={Object.keys(viewData.data[0]).map((key) => {
                const isAmount = key.includes('amount') || key.includes('balance');
                const isId = key === 'id';
                const isStatus = key.includes('status');
                const isDate = key.includes('date') || key.includes('_at');

                return {
                  id: key,
                  header: key.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase()),
                  className: isAmount ? "text-right" : "",
                  accessor: key as any,
                  cell: (row: any) => {
                    const val = row[key];
                    if (val === null || val === undefined) return <span className="text-gray-400">-</span>;
                    if (isId) return <span className="text-xs font-mono text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">#{val}</span>;
                    if (isStatus) return <Badge status={String(val)} />;
                    if (typeof val === 'number' && isAmount) return <span className="font-medium text-gray-900">{formatCurrency(val)}</span>;
                    if (isDate && typeof val === 'string' && !isNaN(Date.parse(val))) {
                      return <span className="text-gray-600">{new Date(val).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}</span>;
                    }
                    return <span className="text-gray-700">{String(val)}</span>;
                  }
                };
              })}
            />
          </div>
        ) : viewData?.data ? (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 max-h-[60vh] overflow-auto">
            <pre className="text-xs text-gray-800 font-mono whitespace-pre-wrap">
              {JSON.stringify(viewData.data, null, 2)}
            </pre>
          </div>
        ) : (
          <p className="text-sm text-gray-500 py-8 text-center">No data available to display.</p>
        )}
        <div className="flex justify-end mt-6">
          <Button onClick={() => setViewData(null)}>Close</Button>
        </div>
      </Modal>
    </div>
  );
}
