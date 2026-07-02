"use client";

import { FileText, Users, CheckCircle, XCircle, Plus, ArrowRight } from "lucide-react";
import useSWR from "swr";
import { fetcher } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import StatCard from "@/components/ui/StatCard";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Table from "@/components/ui/Table";
import Link from "next/link";

export default function LoanOfficerDashboard() {
  const { data: loans, isLoading } = useSWR("/loans/applications/", fetcher);
  const { data: clients } = useSWR("/clients/", fetcher);

  const applications = loans?.results || loans || [];
  const recentClients = clients?.results?.slice(0, 5) || [];

  const counts = {
    total: applications.length,
    draft: applications.filter((l: Record<string,unknown>) => l.status === "DRAFT").length,
    approved: applications.filter((l: Record<string,unknown>) => l.status === "APPROVED").length,
    rejected: applications.filter((l: Record<string,unknown>) => l.status === "REJECTED").length,
  };

  const tasks = applications
    .filter((l: Record<string,unknown>) => l.status === "DRAFT" || l.status === "SUBMITTED")
    .map((l: Record<string,unknown>) => ({
      task: l.status === "DRAFT" ? `Complete application ${l.application_number || 'draft'}` : `Follow up on ${l.application_number}`,
      done: false
    }))
    .slice(0, 4);
    
  if (tasks.length === 0) {
    tasks.push({ task: "Review daily schedule", done: true });
    tasks.push({ task: "Follow up with active clients", done: true });
  }

  const pipelineColumns = [
    { id: "app_no", header: "App #", cell: (r: Record<string,unknown>) => <span className="font-mono text-[13px] font-semibold text-blue-600">{String(r.application_number || "LA0000001")}</span> },
    { id: "client", header: "Client", cell: (r: Record<string,unknown>) => <span className="text-[13px]">{String((r.client as Record<string,unknown>)?.first_name || "—")} {String((r.client as Record<string,unknown>)?.last_name || "")}</span> },
    { id: "amount", header: "Amount", cell: (r: Record<string,unknown>) => <span className="text-[13px] font-medium">{formatCurrency(Number(r.requested_amount || 0))}</span> },
    { id: "status", header: "Status", cell: (r: Record<string,unknown>) => <Badge status={String(r.status || "DRAFT")} /> },
    { id: "date", header: "Date", cell: (r: Record<string,unknown>) => <span className="text-[12px] text-gray-400">{formatDate(String(r.created_at || new Date()))}</span> },
    { id: "action", header: "", cell: (r: Record<string,unknown>) => <Link href={`/loans/${r.id}`}><Button size="sm" variant="ghost" icon={<ArrowRight className="h-3.5 w-3.5" />}>View</Button></Link> },
  ];

  return (
    <div className="flex flex-col gap-4 pb-6"> {/* FIX[BUG 1, 2]: removed h-full, p-6, added pb-6 */}
      {/* Header */}
      <div className="flex items-center justify-between"> {/* FIX[BUG 1]: removed flex-shrink-0 */}
        <div>
          <p className="text-[var(--text-muted)] text-sm mt-0.5">Manage your loan applications and clients</p>
        </div>
        <Link href="/loans/new">
          <Button icon={<Plus className="h-4 w-4" />}>New Application</Button>
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"> {/* FIX[BUG 1]: removed flex-shrink-0 */}
        <StatCard title="My Applications" value={counts.total} icon={<FileText className="h-5 w-5 text-blue-600" />} iconBg="bg-blue-50" progress={70} />
        <StatCard title="Drafts Pending" value={counts.draft} icon={<FileText className="h-5 w-5 text-amber-600" />} iconBg="bg-amber-50" trend="neutral" />
        <StatCard title="Approved (Month)" value={counts.approved} change={25} changeLabel="vs last month" trend="up" icon={<CheckCircle className="h-5 w-5 text-emerald-600" />} iconBg="bg-emerald-50" />
        <StatCard title="Rejected (Month)" value={counts.rejected} change={-10} changeLabel="vs last month" trend="down" icon={<XCircle className="h-5 w-5 text-red-600" />} iconBg="bg-red-50" />
      </div>

      <div className="flex gap-4"> {/* FIX[BUG 1]: removed flex-1 min-h-0 */}
        {/* Pipeline */}
        <div className="flex flex-col flex-1 min-w-0 bg-white rounded-xl border border-gray-200 overflow-hidden"> {/* FIX[BUG 1]: min-w-0 instead of min-h-0 */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200"> {/* FIX[BUG 1]: removed flex-shrink-0 */}
            <div>
              <h3 className="text-[15px] font-semibold text-[var(--text-primary)]">My Application Pipeline</h3>
              <p className="text-[13px] text-[var(--text-muted)] mt-0.5">All your loan applications</p>
            </div>
            <Link href="/loans"><Button variant="ghost" size="sm">View All</Button></Link>
          </div>
          <div> {/* FIX[BUG 1]: removed flex-1 overflow-y-auto wrapper to allow natural height */}
            <Table columns={pipelineColumns} data={applications.slice(0, 8)} loading={isLoading} emptyMessage="No applications yet. Start by creating a new one." />
          </div>
        </div>

        {/* Recent Clients + Tasks */}
        <div className="w-72 flex-shrink-0 flex flex-col gap-4">
          <Card title="Recent Clients" action={<Link href="/clients/new"><Button size="sm" variant="outline" icon={<Plus className="h-3.5 w-3.5" />}>New</Button></Link>}>
            <div className="space-y-3">
              {recentClients.length > 0 ? recentClients.map((c: Record<string,unknown>) => (
                <Link key={String(c.id)} href={`/clients/${c.id}`} className="flex items-center gap-3 hover:bg-gray-50 -mx-2 px-2 py-1.5 rounded-lg transition-colors">
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                    <span className="text-blue-700 text-[11px] font-bold">{String(c.first_name || "?")[0]}{String(c.last_name || "?")[0]}</span>
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-[13px] font-medium text-[var(--text-primary)] truncate">{String(c.first_name)} {String(c.last_name)}</p>
                    <p className="text-[11px] text-[var(--text-muted)]">{String(c.client_number || "")}</p>
                  </div>
                  <Badge status={String(c.status || "PENDING")} className="ml-auto text-[11px]" />
                </Link>
              )) : (
                <div className="text-[13px] text-gray-500 py-4 text-center border border-dashed rounded-lg">No recent clients found</div>
              )}
            </div>
          </Card>

          <Card title="Today's Tasks">
            <div className="space-y-2.5">
              {tasks.map((t: {task: string, done: boolean}, i: number) => (
                <div key={i} className="flex items-center gap-3">
                  <div className={`w-4 h-4 rounded border-2 flex items-center justify-center flex-shrink-0 ${t.done ? "bg-emerald-500 border-emerald-500" : "border-gray-300"}`}>
                    {t.done && <CheckCircle className="h-3 w-3 text-white" />}
                  </div>
                  <span className={`text-[13px] ${t.done ? "line-through text-gray-400" : "text-[var(--text-primary)]"}`}>{t.task}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {/* Client Registration CTA */}
      <div className="mt-auto"> {/* FIX[BUG 1]: removed flex-shrink-0 */}
        <Card>
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center flex-shrink-0">
              <Users className="h-6 w-6 text-blue-600" />
            </div>
            <div className="flex-1">
              <p className="text-[15px] font-semibold text-[var(--text-primary)]">Register a New Client</p>
              <p className="text-[13px] text-[var(--text-muted)]">Add a new borrower to the system to create a loan application</p>
            </div>
            <Link href="/clients/new"><Button variant="outline">Register Client</Button></Link>
          </div>
        </Card>
      </div>
    </div>
  );
}
