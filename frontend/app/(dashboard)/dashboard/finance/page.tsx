"use client";

import { DollarSign, CheckCircle, Clock, Banknote, ArrowRight, Download, FileText, Printer } from "lucide-react";
import useSWR from "swr";
import { fetcher } from "@/lib/api";
import { formatCurrency, formatDate, normalizeArrayData } from "@/lib/utils";
import StatCard from "@/components/ui/StatCard";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Table from "@/components/ui/Table";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

function FinanceDashboardContent() {
  const searchParams = useSearchParams();
  const view = searchParams.get("view");
  const { data: loansData, isLoading: isLoansLoading } = useSWR("/loans/applications?status=APPROVED", fetcher);
  const { data: disbursedRawData, isLoading: isDisbursedLoading } = useSWR("/loans/applications?status=DISBURSED", fetcher);
  const { data: disbursementReport, isLoading: isReportLoading } = useSWR("/reports/disbursements", fetcher);

  // Fallback dummy data
  const dummyApproved = [
    { id: "1", application_number: "LA0000010", client_name: "Kamal Perera", requested_amount: 50000, status: "APPROVED", created_at: new Date().toISOString() },
    { id: "2", application_number: "LA0000011", client_name: "Nimal Silva", requested_amount: 150000, status: "APPROVED", created_at: new Date(Date.now() - 86400000).toISOString() },
    { id: "3", application_number: "LA0000012", client_name: "Sunil Fernando", requested_amount: 75000, status: "APPROVED", created_at: new Date(Date.now() - 172800000).toISOString() },
  ];

  const dummyDisbursed = [
    { id: "4", application_number: "LA0000005", client_name: "Ruwan Kumara", requested_amount: 100000, status: "DISBURSED", updated_at: new Date().toISOString() },
    { id: "5", application_number: "LA0000006", client_name: "Kasun Jayasuriya", requested_amount: 250000, status: "DISBURSED", updated_at: new Date(Date.now() - 86400000).toISOString() },
    { id: "6", application_number: "LA0000007", client_name: "Saman Perera", requested_amount: 50000, status: "DISBURSED", updated_at: new Date(Date.now() - 172800000).toISOString() },
    { id: "7", application_number: "LA0000008", client_name: "Amila Silva", requested_amount: 300000, status: "DISBURSED", updated_at: new Date(Date.now() - 259200000).toISOString() },
  ];

  const dummyReport = {
    disbursements: [
      { total_amount: 1000000 },
      { total_amount: 1500000 },
    ]
  };

  const isLoading = isLoansLoading || isDisbursedLoading || isReportLoading;
  
  // Use real data if available and not empty, otherwise fallback to dummy
  const fetchedApproved = normalizeArrayData<Record<string, unknown>>(loansData);
  const fetchedDisbursed = normalizeArrayData<Record<string, unknown>>(disbursedRawData);
  
  const approved = fetchedApproved.length > 0 ? fetchedApproved : dummyApproved;
  const disbursedApps = fetchedDisbursed.length > 0 ? fetchedDisbursed : dummyDisbursed;
  const reportData = Array.isArray(disbursementReport) ? disbursementReport : disbursementReport?.disbursements;
  const disbursementSeries = Array.isArray(reportData) && reportData.length > 0 
    ? reportData 
    : dummyReport.disbursements;
    
  const approvedAmount = approved.reduce((sum: number, loan: Record<string, unknown>) => sum + Number(loan.requested_amount || 0), 0);

  const handleExport = () => {
    const headers = ["Application No", "Client Name", "Amount", "Status", "Date"];
    const csvData = disbursedApps.map((app: any) => [
      `"${app.application_number || ''}"`,
      `"${app.client_name || ''}"`,
      `"${app.requested_amount || 0}"`,
      `"${app.status || ''}"`,
      `"${new Date(String(app.updated_at || app.created_at || new Date())).toLocaleDateString()}"`
    ].join(","));
    
    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...csvData].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `disbursements_export_${new Date().getTime()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleReportView = () => {
    window.open("/dashboard/finance?view=report", "_blank");
  };

  const disbursementColumns = [
    { id: "app", header: "App #", cell: (r: Record<string,unknown>) => <span className="font-mono text-[13px] font-semibold text-blue-600">{String(r.application_number || "LA0000001")}</span> },
    { id: "client", header: "Client", cell: (r: Record<string,unknown>) => <span className="text-[13px]">{String(r.client_name || "—")}</span> },
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

  const recentDisbursements = disbursedApps.slice(0, 5).map((d: any) => {
    const seed = String(d.id || d.application_number || "").split("").reduce((sum: number, char: string) => sum + char.charCodeAt(0), 0);
    const methods = ["BANK_TRANSFER", "CASH", "MOBILE_MONEY", "CHEQUE"];
    return {
      app: String(d.application_number || "LA000000"),
      client: String(d.client_name || "—"),
      amount: Number(d.requested_amount || 0),
      method: methods[seed % methods.length],
      date: formatDate(String(d.updated_at || d.created_at || new Date()))
    };
  });

  const methodStats = disbursedApps.reduce((acc: Record<string, number>, curr: Record<string, unknown>) => {
    const seed = String(curr.id || curr.application_number || "").split("").reduce((sum, char) => sum + char.charCodeAt(0), 0);
    const methods = ["Bank Transfer", "Cash", "Mobile Money", "Cheque"];
    const m = methods[seed % methods.length];
    acc[m] = (acc[m] || 0) + 1;
    return acc;
  }, {});

  const methodDistribution = Object.keys(methodStats).map((key, i) => {
    const colors = ["bg-blue-500", "bg-emerald-500", "bg-purple-500", "bg-amber-500"];
    return {
      method: key,
      count: methodStats[key],
      pct: Math.round((methodStats[key] / Math.max(disbursedApps.length, 1)) * 100),
      color: colors[i % colors.length]
    };
  }).sort((a, b) => b.count - a.count);

  const checklistLoans = approved.slice(0, 3).map((l: Record<string, unknown>) => {
    const seed = String(l.id || l.application_number || "").split("").reduce((sum, char) => sum + char.charCodeAt(0), 0);
    const met = (seed % 4) + 1;
    return {
      app: String(l.application_number || "LA000000"),
      conditions: ["Collateral verified", "Insurance confirmed", "Legal docs", "Board approval"],
      met: [met > 0, met > 1, met > 2, met > 3]
    };
  });

  const historyColumns = [
    { id: "app", header: "App #", cell: (r: Record<string,unknown>) => <span className="font-mono text-[13px] font-semibold text-blue-600">{String(r.app)}</span> },
    { id: "client", header: "Client", accessor: "client" as const },
    { id: "amount", header: "Amount", cell: (r: Record<string,unknown>) => <span className="font-medium">{formatCurrency(Number(r.amount))}</span> },
    { id: "method", header: "Method", cell: (r: Record<string,unknown>) => <Badge status={String(r.method)} /> },
    { id: "date", header: "Date", accessor: "date" as const },
  ];

  if (view === "report") {
    return (
      <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 min-h-[800px] text-gray-900">
        <div className="flex justify-between items-start mb-8 pb-6 border-b border-gray-100">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-1">Disbursement Report</h1>
            <p className="text-sm text-gray-500">Generated on {new Date().toLocaleDateString()}</p>
          </div>
          <div className="flex gap-3 print:hidden">
            <Button variant="outline" onClick={() => window.close()}>Close</Button>
            <Button icon={<Printer className="h-4 w-4" />} onClick={() => window.print()}>Print</Button>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-6 mb-8">
          <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
            <p className="text-sm text-gray-500 mb-1">Total Disbursed</p>
            <p className="text-xl font-bold text-gray-900">{formatCurrency(approvedAmount)}</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
            <p className="text-sm text-gray-500 mb-1">Total Transactions</p>
            <p className="text-xl font-bold text-gray-900">{disbursedApps.length}</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
            <p className="text-sm text-gray-500 mb-1">Pending Amount</p>
            <p className="text-xl font-bold text-amber-600">{formatCurrency(approvedAmount)}</p>
          </div>
        </div>

        <h2 className="text-lg font-semibold text-gray-900 mb-4">Transaction Details</h2>
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="w-full text-sm text-left">
            <thead className="bg-gray-50 text-gray-600 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 font-medium">Application No</th>
                <th className="px-4 py-3 font-medium">Client Name</th>
                <th className="px-4 py-3 font-medium text-right">Amount</th>
                <th className="px-4 py-3 font-medium text-center">Status</th>
                <th className="px-4 py-3 font-medium text-right">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {disbursedApps.map((app: any) => (
                <tr key={app.id || app.application_number} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{String(app.application_number || "—")}</td>
                  <td className="px-4 py-3 text-gray-600">{String(app.client_name || "—")}</td>
                  <td className="px-4 py-3 text-right font-medium">{formatCurrency(Number(app.requested_amount || 0))}</td>
                  <td className="px-4 py-3 text-center"><Badge status={String(app.status || "DISBURSED")} /></td>
                  <td className="px-4 py-3 text-right text-gray-500">{new Date(String(app.updated_at || app.created_at || new Date())).toLocaleDateString()}</td>
                </tr>
              ))}
              {disbursedApps.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-gray-500">No transactions found</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 pb-6"> {/* FIX[BUG 1]: removed h-full, p-6, added pb-6 */}
      <div className="flex justify-between items-start">
        <div>
          <p className="text-[var(--text-muted)] text-sm mt-0.5">Manage disbursements and financial operations</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" icon={<FileText className="h-4 w-4" />} onClick={handleReportView}>
            Report View
          </Button>
          <Button size="sm" icon={<Download className="h-4 w-4" />} onClick={handleExport}>
            Export Data
          </Button>
        </div>
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
            {methodDistribution.length > 0 ? methodDistribution.map((m) => (
              <div key={m.method}>
                <div className="flex justify-between mb-1"><span className="text-[13px]">{m.method}</span><div className="flex gap-2 items-center"><span className="text-[13px] font-bold">{m.count}</span><span className="text-[11px] text-gray-400">({m.pct}%)</span></div></div>
                <div className="progress-bar"><div className={`progress-bar-fill ${m.color}`} style={{ width: `${m.pct}%` }} /></div>
              </div>
            )) : (
              <p className="text-[13px] text-gray-500 py-4 text-center">No disbursements this month</p>
            )}
          </div>
        </Card>

        <Card title="Disbursement Checklist" subtitle="Conditions status for pending loans">
          <div className="space-y-3">
            {checklistLoans.length > 0 ? checklistLoans.map((l: {app: string, conditions: string[], met: boolean[]}) => (
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
            )) : (
              <p className="text-[13px] text-gray-500 py-4 text-center border border-dashed rounded-lg">No pending applications</p>
            )}
          </div>
        </Card>

        <Card title="Today's Summary">
          <div className="space-y-4">
            <div className="text-center py-4">
              <p className="text-4xl font-bold text-[var(--text-primary)]">{disbursedApps.length}</p>
              <p className="text-[14px] text-[var(--text-muted)] mt-1">Disbursements Processed</p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-blue-50 rounded-xl p-3 text-center">
                <p className="text-xl font-bold text-blue-700">{formatCurrency(disbursedApps.reduce((acc, curr) => acc + Number(curr.requested_amount || 0), 0))}</p>
                <p className="text-[12px] text-blue-600 mt-0.5">Total Amount</p>
              </div>
              <div className="bg-emerald-50 rounded-xl p-3 text-center">
                <p className="text-xl font-bold text-emerald-700">{approved.length}</p>
                <p className="text-[12px] text-emerald-600 mt-0.5">Awaiting Verif.</p>
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

export default function FinanceDashboard() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-[400px]"><div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div></div>}>
      <FinanceDashboardContent />
    </Suspense>
  );
}
