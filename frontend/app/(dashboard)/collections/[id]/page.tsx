"use client";

import React, { useState } from "react";
import useSWR, { useSWRConfig } from "swr";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft, Phone, Mail, MapPin, Clock, AlertTriangle,
  CheckCircle, FileText, User, MessageSquare, TrendingUp, X
} from "lucide-react";
import { fetcher } from "@/lib/api";
import api from "@/lib/api";
import { formatRelativeTime, formatCurrency } from "@/lib/utils";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Spinner from "@/components/ui/Spinner";
import { useToast } from "@/components/ui/Toast";

interface CollectionAction {
  id: number;
  action_type: string;
  outcome: string;
  notes: string;
  performed_by: { first_name: string; last_name: string } | null;
  performed_at: string;
}

interface PromiseToPay {
  id: number;
  promised_amount: string;
  promised_date: string;
  status: string;
  recorded_at: string;
}

interface DelinquencyCase {
  id: number;
  loan: {
    id: number;
    loan_number: string;
    client: { first_name: string; last_name: string; nic: string } | null;
    principal_amount: string;
  };
  status: string;
  bucket: string;
  total_overdue_amount: string;
  days_overdue: number;
  overdue_installments_count: number;
  predicted_default_probability: number | null;
  behavioral_pattern_label: string;
  llm_recommended_action: string;
  assigned_to: { first_name: string; last_name: string } | null;
  opened_at: string;
  updated_at: string;
  resolved_at: string | null;
  resolution_notes: string;
  actions: CollectionAction[];
  promises: PromiseToPay[];
}

const BUCKET_STYLES: Record<string, string> = {
  BUCKET_1_7: "bg-yellow-50 text-yellow-700 border border-yellow-200",
  BUCKET_8_30: "bg-orange-50 text-orange-700 border border-orange-200",
  BUCKET_OVER_30: "bg-red-50 text-red-700 border border-red-200",
};

const BUCKET_LABELS: Record<string, string> = {
  BUCKET_1_7: "1–7 Days Overdue",
  BUCKET_8_30: "8–30 Days Overdue",
  BUCKET_OVER_30: "30+ Days Overdue",
};

const STATUS_STYLES: Record<string, string> = {
  OPEN: "bg-amber-50 text-amber-700",
  IN_PROGRESS: "bg-blue-50 text-blue-700",
  PROMISE_TO_PAY: "bg-purple-50 text-purple-700",
  ESCALATED: "bg-red-50 text-red-700",
  RESOLVED: "bg-emerald-50 text-emerald-700",
  WRITTEN_OFF: "bg-gray-100 text-gray-600",
  LEGAL: "bg-rose-50 text-rose-700",
};

const ACTION_TYPE_ICONS: Record<string, React.ReactNode> = {
  PHONE_CALL: <Phone className="h-3.5 w-3.5 text-blue-500" />,
  SMS: <MessageSquare className="h-3.5 w-3.5 text-green-500" />,
  EMAIL: <Mail className="h-3.5 w-3.5 text-indigo-500" />,
  FIELD_VISIT: <MapPin className="h-3.5 w-3.5 text-orange-500" />,
  WRITTEN_NOTICE: <FileText className="h-3.5 w-3.5 text-yellow-600" />,
  GUARANTOR_CONTACT: <User className="h-3.5 w-3.5 text-purple-500" />,
  INTERNAL_NOTE: <FileText className="h-3.5 w-3.5 text-gray-400" />,
};

export default function CollectionCaseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const toast = useToast();
  const { mutate } = useSWRConfig();
  const id = params.id as string;

  const [actionType, setActionType] = useState("PHONE_CALL");
  const [outcome, setOutcome] = useState("NO_ANSWER");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [ptpAmount, setPtpAmount] = useState("");
  const [ptpDate, setPtpDate] = useState("");
  const [showPtpForm, setShowPtpForm] = useState(false);
  const [showResolveModal, setShowResolveModal] = useState(false);
  const [resolutionNotes, setResolutionNotes] = useState("");

  const { data: caseData, isLoading, error, mutate: mutateCase } = useSWR<DelinquencyCase>(
    `/collections/${id}/history/`,
    fetcher
  );

  const handleLogContact = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!notes.trim()) return;
    try {
      setSubmitting(true);
      await api.post(`collections/${id}/contact/`, { action_type: actionType, outcome, notes });
      toast.success("Contact attempt logged");
      setNotes("");
      mutateCase();
    } catch (err: any) {
      toast.error(err?.response?.data?.error || "Failed to log contact");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRecordPtp = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      await api.post(`collections/${id}/promise-to-pay/`, {
        promised_amount: ptpAmount,
        promised_date: ptpDate,
      });
      toast.success("Promise to Pay recorded");
      setShowPtpForm(false);
      setPtpAmount("");
      setPtpDate("");
      mutateCase();
    } catch (err: any) {
      toast.error(err?.response?.data?.error || "Failed to record PTP");
    } finally {
      setSubmitting(false);
    }
  };

  const handleResolve = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      await api.post(`collections/${id}/resolve/`, { resolution_notes: resolutionNotes });
      toast.success("Case resolved successfully");
      setShowResolveModal(false);
      mutateCase();
    } catch (err: any) {
      toast.error(err?.response?.data?.error || "Failed to resolve case");
    } finally {
      setSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !caseData) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-4">
        <AlertTriangle className="h-10 w-10 text-amber-400" />
        <p className="text-[var(--text-secondary)] font-medium">Delinquency case not found.</p>
        <Button variant="outline" onClick={() => router.back()} icon={<ArrowLeft className="h-4 w-4" />}>
          Back to Collections
        </Button>
      </div>
    );
  }

  const clientName = caseData.loan?.client
    ? `${caseData.loan.client.first_name} ${caseData.loan.client.last_name}`
    : "Unknown Client";

  const activePtp = caseData.promises?.find((p) => p.status === "ACTIVE");
  const isClosed = ["RESOLVED", "WRITTEN_OFF", "LEGAL"].includes(caseData.status);

  return (
    <div className="flex flex-col gap-4 pb-8">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.back()}
            className="p-2 rounded-lg border border-[var(--border-color)] hover:bg-gray-50 transition-colors"
          >
            <ArrowLeft className="h-4 w-4 text-[var(--text-secondary)]" />
          </button>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-semibold text-[var(--text-primary)] text-base">
                {clientName} — {caseData.loan?.loan_number}
              </span>
              <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${BUCKET_STYLES[caseData.bucket] || "bg-gray-100 text-gray-600"}`}>
                {BUCKET_LABELS[caseData.bucket] || caseData.bucket}
              </span>
              <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${STATUS_STYLES[caseData.status] || "bg-gray-100"}`}>
                {caseData.status.replace(/_/g, " ")}
              </span>
            </div>
            <p className="text-[12px] text-[var(--text-muted)] mt-0.5">
              Opened {formatRelativeTime(caseData.opened_at)} · {caseData.days_overdue} days overdue ·{" "}
              {caseData.overdue_installments_count} overdue installment(s)
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          {!isClosed && (
            <>
              <Button
                variant="outline"
                onClick={() => setShowPtpForm(true)}
                icon={<Clock className="h-4 w-4" />}
              >
                Record PTP
              </Button>
              <Button
                variant="primary"
                onClick={() => setShowResolveModal(true)}
                icon={<CheckCircle className="h-4 w-4" />}
              >
                Resolve Case
              </Button>
            </>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left — Actions & Log Form */}
        <div className="lg:col-span-2 space-y-4">
          {/* Active Promise to Pay */}
          {activePtp && (
            <div className="p-4 rounded-xl border border-purple-200 bg-purple-50 flex items-center gap-4">
              <Clock className="h-6 w-6 text-purple-600 flex-shrink-0" />
              <div>
                <p className="font-semibold text-purple-900 text-[14px]">Active Promise to Pay</p>
                <p className="text-[13px] text-purple-700">
                  Client promised <strong>{formatCurrency(Number(activePtp.promised_amount))}</strong> by{" "}
                  <strong>{new Date(activePtp.promised_date).toLocaleDateString("en-LK")}</strong>
                </p>
              </div>
            </div>
          )}

          {/* Log Contact Attempt */}
          {!isClosed && (
            <Card title="Log Contact Attempt">
              <form onSubmit={handleLogContact} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-[12px] font-semibold text-gray-400">ACTION TYPE</label>
                    <select
                      value={actionType}
                      onChange={(e) => setActionType(e.target.value)}
                      className="w-full p-2.5 border rounded-lg text-[13px] focus:ring-1 focus:ring-blue-500 focus:outline-none"
                    >
                      <option value="PHONE_CALL">Phone Call</option>
                      <option value="SMS">SMS Sent</option>
                      <option value="EMAIL">Email Sent</option>
                      <option value="FIELD_VISIT">Field Visit</option>
                      <option value="WRITTEN_NOTICE">Written Notice</option>
                      <option value="GUARANTOR_CONTACT">Guarantor Contacted</option>
                      <option value="INTERNAL_NOTE">Internal Note</option>
                    </select>
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-[12px] font-semibold text-gray-400">OUTCOME</label>
                    <select
                      value={outcome}
                      onChange={(e) => setOutcome(e.target.value)}
                      className="w-full p-2.5 border rounded-lg text-[13px] focus:ring-1 focus:ring-blue-500 focus:outline-none"
                    >
                      <option value="NO_ANSWER">No Answer</option>
                      <option value="CONTACTED">Client Contacted</option>
                      <option value="PROMISED_PAYMENT">Promised to Pay</option>
                      <option value="REFUSED">Refused to Pay</option>
                      <option value="DISPUTE">Payment in Dispute</option>
                      <option value="UNREACHABLE">Client Unreachable</option>
                      <option value="OTHER">Other</option>
                    </select>
                  </div>
                </div>
                <div className="space-y-1.5">
                  <label className="text-[12px] font-semibold text-gray-400">NOTES *</label>
                  <textarea
                    required
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Describe what happened during this contact attempt..."
                    className="w-full min-h-[80px] p-3 border rounded-lg text-[13px] focus:ring-1 focus:ring-blue-500 focus:outline-none resize-none"
                  />
                </div>
                <div className="flex justify-end">
                  <Button variant="primary" type="submit" disabled={submitting}>
                    {submitting ? "Saving..." : "Log Contact"}
                  </Button>
                </div>
              </form>
            </Card>
          )}

          {/* Action History */}
          <Card title={`Contact History (${caseData.actions?.length ?? 0})`}>
            {!caseData.actions || caseData.actions.length === 0 ? (
              <p className="text-center text-[13px] text-gray-400 py-8">No contact attempts logged yet.</p>
            ) : (
              <div className="space-y-3">
                {caseData.actions.map((action) => (
                  <div
                    key={action.id}
                    className="flex gap-3 p-3 rounded-lg border border-[var(--border-color)] bg-gray-50/50"
                  >
                    <div className="mt-0.5 flex-shrink-0">
                      {ACTION_TYPE_ICONS[action.action_type] || <Phone className="h-3.5 w-3.5 text-gray-400" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[13px] font-semibold text-[var(--text-primary)]">
                          {action.action_type.replace(/_/g, " ")}
                          <span className="ml-2 text-[11px] font-normal px-1.5 py-0.5 bg-gray-100 rounded text-gray-500">
                            {action.outcome.replace(/_/g, " ")}
                          </span>
                        </span>
                        <span className="text-[11px] text-gray-400 flex-shrink-0">
                          {formatRelativeTime(action.performed_at)}
                        </span>
                      </div>
                      <p className="text-[13px] text-[var(--text-secondary)] mt-0.5">{action.notes}</p>
                      {action.performed_by && (
                        <p className="text-[11px] text-gray-400 mt-1">
                          by {action.performed_by.first_name} {action.performed_by.last_name}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Right — Case Summary */}
        <div className="lg:col-span-1 space-y-4">
          {/* Financial Summary */}
          <Card title="Case Summary">
            <div className="space-y-3">
              {[
                { label: "Total Overdue", value: formatCurrency(Number(caseData.total_overdue_amount)), highlight: true },
                { label: "Days Overdue", value: `${caseData.days_overdue} days` },
                { label: "Overdue Installments", value: caseData.overdue_installments_count },
                { label: "Loan Principal", value: caseData.loan?.principal_amount ? formatCurrency(Number(caseData.loan.principal_amount)) : "—" },
                { label: "Bucket", value: BUCKET_LABELS[caseData.bucket] || caseData.bucket },
                { label: "Status", value: caseData.status.replace(/_/g, " ") },
                { label: "Assigned To", value: caseData.assigned_to ? `${caseData.assigned_to.first_name} ${caseData.assigned_to.last_name}` : "Unassigned" },
                { label: "Opened", value: new Date(caseData.opened_at).toLocaleDateString("en-LK") },
              ].map(({ label, value, highlight }) => (
                <div key={label} className="flex justify-between items-center py-1.5 border-b border-gray-50 last:border-0">
                  <span className="text-[12px] text-gray-500">{label}</span>
                  <span className={`text-[13px] font-semibold ${highlight ? "text-red-600" : "text-[var(--text-primary)]"}`}>
                    {String(value)}
                  </span>
                </div>
              ))}
            </div>
          </Card>

          {/* AI Insights */}
          {(caseData.predicted_default_probability !== null || caseData.llm_recommended_action) && (
            <Card title="AI Insights">
              <div className="space-y-3">
                {caseData.predicted_default_probability !== null && (
                  <div className="p-3 bg-orange-50 border border-orange-100 rounded-lg">
                    <p className="text-[11px] font-semibold text-orange-400 mb-1">DEFAULT PROBABILITY</p>
                    <p className="text-[20px] font-bold text-orange-600">
                      {Math.round(caseData.predicted_default_probability * 100)}%
                    </p>
                  </div>
                )}
                {caseData.behavioral_pattern_label && (
                  <div>
                    <p className="text-[11px] font-semibold text-gray-400 mb-1">PATTERN</p>
                    <span className="text-[12px] bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full">
                      {caseData.behavioral_pattern_label}
                    </span>
                  </div>
                )}
                {caseData.llm_recommended_action && (
                  <div>
                    <p className="text-[11px] font-semibold text-gray-400 mb-1">AI RECOMMENDATION</p>
                    <p className="text-[13px] text-[var(--text-secondary)] leading-relaxed">
                      {caseData.llm_recommended_action}
                    </p>
                  </div>
                )}
              </div>
            </Card>
          )}

          {/* Promise History */}
          {caseData.promises && caseData.promises.length > 0 && (
            <Card title={`Promise to Pay (${caseData.promises.length})`}>
              <div className="space-y-2">
                {caseData.promises.map((ptp) => (
                  <div key={ptp.id} className="p-2.5 border border-[var(--border-color)] rounded-lg">
                    <div className="flex justify-between items-center">
                      <span className="text-[13px] font-semibold">{formatCurrency(Number(ptp.promised_amount))}</span>
                      <span className={`text-[11px] px-1.5 py-0.5 rounded-full font-medium ${
                        ptp.status === "KEPT" ? "bg-emerald-50 text-emerald-700" :
                        ptp.status === "BROKEN" ? "bg-red-50 text-red-700" :
                        ptp.status === "EXTENDED" ? "bg-amber-50 text-amber-700" : "bg-purple-50 text-purple-700"
                      }`}>{ptp.status}</span>
                    </div>
                    <p className="text-[11px] text-gray-400 mt-0.5">
                      Due: {new Date(ptp.promised_date).toLocaleDateString("en-LK")} · Recorded {formatRelativeTime(ptp.recorded_at)}
                    </p>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* PTP Modal */}
      {showPtpForm && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl border max-w-md w-full overflow-hidden">
            <div className="px-6 py-4 border-b flex justify-between items-center bg-gray-50">
              <h3 className="font-semibold text-[15px] flex items-center gap-2">
                <Clock className="h-4 w-4 text-purple-600" /> Record Promise to Pay
              </h3>
              <button onClick={() => setShowPtpForm(false)}>
                <X className="h-4 w-4 text-gray-400 hover:text-gray-600" />
              </button>
            </div>
            <form onSubmit={handleRecordPtp}>
              <div className="p-6 space-y-4">
                <div className="space-y-1.5">
                  <label className="text-[12px] font-semibold text-gray-400">PROMISED AMOUNT (LKR) *</label>
                  <input
                    type="number"
                    required
                    value={ptpAmount}
                    onChange={(e) => setPtpAmount(e.target.value)}
                    placeholder="e.g. 15000"
                    className="w-full p-2.5 border rounded-lg text-[13px] focus:ring-1 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-[12px] font-semibold text-gray-400">PROMISED DATE *</label>
                  <input
                    type="date"
                    required
                    value={ptpDate}
                    onChange={(e) => setPtpDate(e.target.value)}
                    className="w-full p-2.5 border rounded-lg text-[13px] focus:ring-1 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
              </div>
              <div className="px-6 py-4 bg-gray-50 border-t flex justify-end gap-2">
                <Button variant="secondary" onClick={() => setShowPtpForm(false)}>Cancel</Button>
                <Button variant="primary" type="submit" disabled={submitting}>
                  {submitting ? "Saving..." : "Record PTP"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Resolve Modal */}
      {showResolveModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl border max-w-md w-full overflow-hidden">
            <div className="px-6 py-4 border-b flex justify-between items-center bg-gray-50">
              <h3 className="font-semibold text-[15px] flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-emerald-600" /> Resolve Delinquency Case
              </h3>
              <button onClick={() => setShowResolveModal(false)}>
                <X className="h-4 w-4 text-gray-400 hover:text-gray-600" />
              </button>
            </div>
            <form onSubmit={handleResolve}>
              <div className="p-6 space-y-4">
                <div className="space-y-1.5">
                  <label className="text-[12px] font-semibold text-gray-400">RESOLUTION NOTES</label>
                  <textarea
                    value={resolutionNotes}
                    onChange={(e) => setResolutionNotes(e.target.value)}
                    placeholder="Describe how the case was resolved..."
                    className="w-full min-h-[80px] p-3 border rounded-lg text-[13px] focus:ring-1 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
              </div>
              <div className="px-6 py-4 bg-gray-50 border-t flex justify-end gap-2">
                <Button variant="secondary" onClick={() => setShowResolveModal(false)}>Cancel</Button>
                <Button variant="primary" type="submit" disabled={submitting} className="bg-emerald-600 hover:bg-emerald-700">
                  {submitting ? "Saving..." : "Mark Resolved"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
