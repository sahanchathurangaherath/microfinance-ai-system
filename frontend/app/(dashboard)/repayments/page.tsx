"use client";

import useSWR from "swr";
import { DollarSign, CheckCircle, Clock, AlertTriangle, Filter, Search } from "lucide-react";
import { fetcher } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import StatCard from "@/components/ui/StatCard";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Table from "@/components/ui/Table";
import Button from "@/components/ui/Button";
import { useState } from "react";
import api from "@/lib/api";
import { useToast } from "@/components/ui/Toast";

export default function RepaymentsPage() {
  const toast = useToast();
  const [statusFilter, setStatusFilter] = useState("");
  const [isTriggering, setIsTriggering] = useState(false);
  const params = statusFilter ? `?status=${statusFilter}` : "";
  const { data, error, isLoading, mutate } = useSWR(`/repayments/${params}`, fetcher);
  const repayments = data?.results || data || [];

  const dueAmount = repayments.reduce((sum: number, r: Record<string,unknown>) => sum + Number(r.total_amount_due || 0), 0);
  const collectedAmount = repayments.reduce((sum: number, r: Record<string,unknown>) => sum + Number(r.amount_paid || 0), 0);
  const overdueCount = repayments.filter((r: Record<string,unknown>) => r.payment_status === "OVERDUE" || r.status === "OVERDUE").length;
  const onTimeCount = repayments.filter((r: Record<string,unknown>) => r.payment_status === "PAID" || r.status === "PAID").length;
  const paidRatio = repayments.length > 0 ? Math.round((onTimeCount / repayments.length) * 100) + "%" : "0%";

  const columns = [
    { id: "loan", header: "Loan #", cell: (r: Record<string,unknown>) => <span className="font-mono text-[13px] font-semibold text-blue-600">{String(r.loan_number || (r.loan as Record<string,unknown>)?.loan_number || "—")}</span> },
    { id: "client", header: "Client", cell: (r: Record<string,unknown>) => <span className="text-[13px]">{String(r.client_name || "—")}</span> },
    { id: "installment", header: "Installment", cell: (r: Record<string,unknown>) => <span className="text-[13px]">#{String(r.installment_number || "—")}</span> },
    { id: "amount_due", header: "Due Amount", cell: (r: Record<string,unknown>) => <span className="text-[13px] font-medium">{formatCurrency(Number(r.total_amount_due || 0))}</span> },
    { id: "amount_paid", header: "Paid", cell: (r: Record<string,unknown>) => <span className="text-[13px] font-medium text-emerald-600">{formatCurrency(Number(r.amount_paid || 0))}</span> },
    { id: "due_date", header: "Due Date", cell: (r: Record<string,unknown>) => <span className="text-[13px]">{formatDate(String(r.due_date || new Date()))}</span> },
    { id: "status", header: "Status", cell: (r: Record<string,unknown>) => <Badge status={String(r.payment_status || r.status || "PENDING")} /> },
  ];

  const handleTriggerA4 = async () => {
    try {
      setIsTriggering(true);
      await api.post("/repayments/a4/scan/");
      mutate();
      toast.success("AI Repayment Check (A4) completed successfully!");
    } catch (err: any) {
      toast.error("Failed to trigger A4: " + (err.response?.data?.error || err.message));
    } finally {
      setIsTriggering(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <p className="text-[var(--text-muted)] text-sm mt-0.5">Track loan installment payments</p>
        </div>
        <Button onClick={handleTriggerA4} disabled={isTriggering}>
          {isTriggering ? "Running..." : "Run AI Repayment Check"}
        </Button>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Due Amount" value={formatCurrency(dueAmount)} loading={isLoading} icon={<Clock className="h-5 w-5 text-amber-600" />} iconBg="bg-amber-50" />
        <StatCard title="Collected Amount" value={formatCurrency(collectedAmount)} loading={isLoading} icon={<DollarSign className="h-5 w-5 text-emerald-600" />} iconBg="bg-emerald-50" />
        <StatCard title="Paid On Time" value={paidRatio} loading={isLoading} icon={<CheckCircle className="h-5 w-5 text-blue-600" />} iconBg="bg-blue-50" />
        <StatCard title="Overdue Count" value={overdueCount} loading={isLoading} icon={<AlertTriangle className="h-5 w-5 text-red-600" />} iconBg="bg-red-50" />
      </div>

      <Card padding={false}>
        <div className="flex items-center gap-3 p-4 border-b border-[var(--border-color)] overflow-hidden">
          <Filter className="h-4 w-4 text-[var(--text-muted)] flex-shrink-0" />
          <div className="flex gap-2 overflow-x-auto scrollbar-none pb-1 -mr-4 pr-4 sm:mr-0 sm:pr-0">
            {["", "PENDING", "PAID", "PARTIAL", "OVERDUE"].map(s => (
              <button key={s} onClick={() => setStatusFilter(s)}
                className={`px-3 py-1.5 rounded-lg text-[12px] font-medium transition-all flex-shrink-0 ${statusFilter === s ? "bg-blue-100 text-blue-700" : "text-gray-500 hover:bg-gray-100"}`}>
                {s || "All"}
              </button>
            ))}
          </div>
        </div>
        <Table columns={columns} data={repayments} loading={isLoading} error={error} onRetry={() => mutate()} emptyMessage="No repayments found matching your search." />
      </Card>
    </div>
  );
}
