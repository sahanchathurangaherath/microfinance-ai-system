"use client";

import { useState } from "react";
import useSWR, { useSWRConfig } from "swr";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft, ShieldAlert, AlertTriangle, CheckCircle, Search,
  Eye, FileText, User, Clock, RefreshCw, Lock, Unlock, X
} from "lucide-react";
import { fetcher } from "@/lib/api";
import api from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import { useToast } from "@/components/ui/Toast";

interface Signal {
  type: string;
  detail: string;
  weight: number;
}

interface FraudAlert {
  id: number;
  alert_type: string;
  severity: string;
  status: string;
  fraud_risk_score: number;
  ai_rationale: string;
  detected_signals: Signal[];
  ai_confidence: number;
  prosecutor_findings: string[];
  defense_findings: string[];
  investigation_focus: string;
  investigation_notes: string;
  triggered_at: string;
  assigned_to: number | null;
  client: number | null;
  application: number | null;
}

const SEVERITY_COLORS: Record<string, string> = {
  LOW: "bg-blue-50 text-blue-700 border border-blue-100",
  MEDIUM: "bg-amber-50 text-amber-700 border border-amber-100",
  HIGH: "bg-orange-50 text-orange-700 border border-orange-100",
  CRITICAL: "bg-red-50 text-red-700 border border-red-100",
};

const STATUS_COLORS: Record<string, string> = {
  OPEN: "bg-amber-50 text-amber-700",
  UNDER_INVESTIGATION: "bg-blue-50 text-blue-700",
  CLEARED: "bg-emerald-50 text-emerald-700",
  CONFIRMED: "bg-red-50 text-red-700",
  CLOSED: "bg-gray-100 text-gray-600",
};

export default function FraudAlertDetailPage() {
  const params = useParams();
  const router = useRouter();
  const toast = useToast();
  const { mutate } = useSWRConfig();
  const id = params.id as string;

  const [closingModal, setClosingModal] = useState(false);
  const [closeOutcome, setCloseOutcome] = useState<"CLEARED" | "CONFIRMED" | "INCONCLUSIVE">("CLEARED");
  const [closeFindings, setCloseFindings] = useState("");
  const [complianceAction, setComplianceAction] = useState("");
  const [actionReason, setActionReason] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const { data: alert, isLoading, error, mutate: mutateAlert } = useSWR<FraudAlert>(
    `/fraud/alerts/${id}/`,
    fetcher
  );

  const handleOpenInvestigation = async () => {
    try {
      setSubmitting(true);
      await api.post(`fraud/alerts/${id}/investigate/`);
      toast.success("Investigation opened successfully");
      mutateAlert();
    } catch (err: any) {
      toast.error(err?.response?.data?.error || "Failed to open investigation");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCloseAlert = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      await api.patch(`fraud/alerts/${id}/close/`, {
        outcome: closeOutcome,
        findings: closeFindings,
        compliance_action: complianceAction || undefined,
        action_reason: actionReason,
      });
      toast.success(`Alert closed — Outcome: ${closeOutcome}`);
      setClosingModal(false);
      mutateAlert();
    } catch (err: any) {
      toast.error(err?.response?.data?.error || "Failed to close alert");
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

  if (error || !alert) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-4">
        <ShieldAlert className="h-10 w-10 text-red-400" />
        <p className="text-[var(--text-secondary)] font-medium">Fraud alert not found.</p>
        <Button variant="outline" onClick={() => router.back()} icon={<ArrowLeft className="h-4 w-4" />}>
          Back to Alerts
        </Button>
      </div>
    );
  }

  const scoreColor =
    alert.fraud_risk_score >= 70 ? "text-red-600" :
    alert.fraud_risk_score >= 50 ? "text-orange-500" :
    alert.fraud_risk_score >= 25 ? "text-amber-500" : "text-emerald-600";

  return (
    <div className="flex flex-col gap-4 pb-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.back()}
            className="p-2 rounded-lg border border-[var(--border-color)] hover:bg-gray-50 transition-colors"
          >
            <ArrowLeft className="h-4 w-4 text-[var(--text-secondary)]" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-[var(--text-primary)] text-base">
                {alert.alert_type.replace(/_/g, " ")} — Alert #{alert.id}
              </span>
              <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${SEVERITY_COLORS[alert.severity] || ""}`}>
                {alert.severity}
              </span>
              <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${STATUS_COLORS[alert.status] || ""}`}>
                {alert.status.replace(/_/g, " ")}
              </span>
            </div>
            <p className="text-[12px] text-[var(--text-muted)] mt-0.5">
              Detected {formatRelativeTime(alert.triggered_at)} · Client #{alert.client ?? "—"}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          {alert.status === "OPEN" && (
            <Button
              variant="primary"
              icon={<Search className="h-4 w-4" />}
              onClick={handleOpenInvestigation}
              disabled={submitting}
            >
              Open Investigation
            </Button>
          )}
          {alert.status === "UNDER_INVESTIGATION" && (
            <Button
              variant="outline"
              className="text-red-600 border-red-200 hover:bg-red-50"
              icon={<Lock className="h-4 w-4" />}
              onClick={() => setClosingModal(true)}
              disabled={submitting}
            >
              Close Alert
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left — Main Content */}
        <div className="lg:col-span-2 space-y-4">
          {/* Risk Score Summary */}
          <Card title="Fraud Risk Assessment">
            <div className="flex items-center gap-6">
              <div className="flex flex-col items-center justify-center w-24 h-24 rounded-full border-4 border-gray-100 bg-gray-50">
                <span className={`text-2xl font-bold ${scoreColor}`}>
                  {Math.round(alert.fraud_risk_score)}
                </span>
                <span className="text-[10px] text-gray-500 font-medium">/ 100</span>
              </div>
              <div className="flex-1 space-y-3">
                <div>
                  <span className="text-[12px] font-semibold text-gray-400">AI RATIONALE</span>
                  <p className="text-[13px] text-[var(--text-secondary)] mt-0.5 leading-relaxed">
                    {alert.ai_rationale || "No rationale provided."}
                  </p>
                </div>
                {alert.investigation_focus && (
                  <div className="p-2 bg-blue-50 border border-blue-100 rounded text-[12px] text-blue-800">
                    <span className="font-semibold">Investigation Focus: </span>
                    {alert.investigation_focus}
                  </div>
                )}
                <div className="flex items-center gap-2 text-[12px] text-gray-500">
                  <span>AI Confidence:</span>
                  <span className="font-semibold text-[var(--text-primary)]">
                    {Math.round(alert.ai_confidence * 100)}%
                  </span>
                </div>
              </div>
            </div>
          </Card>

          {/* Detected Signals */}
          <Card title={`Detected Signals (${alert.detected_signals.length})`}>
            {alert.detected_signals.length === 0 ? (
              <p className="text-[13px] text-gray-500 py-4 text-center">No signals detected.</p>
            ) : (
              <div className="space-y-2">
                {alert.detected_signals.map((signal, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-3 rounded-lg border border-[var(--border-color)] bg-gray-50/50"
                  >
                    <div className="flex items-center gap-3">
                      <AlertTriangle className="h-4 w-4 text-amber-500 flex-shrink-0" />
                      <div>
                        <p className="text-[13px] font-semibold text-[var(--text-primary)]">
                          {signal.type.replace(/_/g, " ")}
                        </p>
                        <p className="text-[12px] text-gray-500">{signal.detail}</p>
                      </div>
                    </div>
                    <span className="text-[12px] font-bold text-red-600 bg-red-50 px-2 py-0.5 rounded-full">
                      +{signal.weight} pts
                    </span>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* LLM Debate Findings */}
          {(alert.prosecutor_findings.length > 0 || alert.defense_findings.length > 0) && (
            <div className="grid grid-cols-2 gap-4">
              <Card title="⚖️ Prosecutor Findings">
                <ul className="space-y-2">
                  {alert.prosecutor_findings.map((f, i) => (
                    <li key={i} className="flex items-start gap-2 text-[13px] text-red-700">
                      <AlertTriangle className="h-3.5 w-3.5 mt-0.5 flex-shrink-0 text-red-500" />
                      {f}
                    </li>
                  ))}
                </ul>
              </Card>
              <Card title="🛡️ Defense Findings">
                <ul className="space-y-2">
                  {alert.defense_findings.map((f, i) => (
                    <li key={i} className="flex items-start gap-2 text-[13px] text-emerald-700">
                      <CheckCircle className="h-3.5 w-3.5 mt-0.5 flex-shrink-0 text-emerald-500" />
                      {f}
                    </li>
                  ))}
                </ul>
              </Card>
            </div>
          )}

          {/* Investigation Notes */}
          {alert.investigation_notes && (
            <Card title="Investigation Notes">
              <p className="text-[13px] text-[var(--text-secondary)] leading-relaxed whitespace-pre-wrap">
                {alert.investigation_notes}
              </p>
            </Card>
          )}
        </div>

        {/* Right — Case Info */}
        <div className="lg:col-span-1 space-y-4">
          <Card title="Alert Details">
            <div className="space-y-3">
              {[
                { label: "Alert ID", value: `#${alert.id}` },
                { label: "Type", value: alert.alert_type.replace(/_/g, " ") },
                { label: "Severity", value: alert.severity },
                { label: "Status", value: alert.status.replace(/_/g, " ") },
                { label: "Risk Score", value: `${Math.round(alert.fraud_risk_score)}/100` },
                { label: "AI Confidence", value: `${Math.round(alert.ai_confidence * 100)}%` },
                { label: "Client ID", value: alert.client ? `#${alert.client}` : "—" },
                { label: "Application ID", value: alert.application ? `#${alert.application}` : "—" },
                { label: "Triggered", value: formatRelativeTime(alert.triggered_at) },
              ].map(({ label, value }) => (
                <div key={label} className="flex justify-between items-center py-1 border-b border-gray-50 last:border-0">
                  <span className="text-[12px] text-gray-500">{label}</span>
                  <span className="text-[13px] font-semibold text-[var(--text-primary)]">{value}</span>
                </div>
              ))}
            </div>
          </Card>

          <Card title="Quick Actions">
            <div className="space-y-2">
              {alert.status === "OPEN" && (
                <Button
                  variant="primary"
                  className="w-full"
                  onClick={handleOpenInvestigation}
                  disabled={submitting}
                  icon={<Search className="h-4 w-4" />}
                >
                  Open Investigation
                </Button>
              )}
              {alert.status === "UNDER_INVESTIGATION" && (
                <Button
                  variant="outline"
                  className="w-full text-red-600 border-red-200 hover:bg-red-50"
                  onClick={() => setClosingModal(true)}
                  disabled={submitting}
                  icon={<Lock className="h-4 w-4" />}
                >
                  Close Alert
                </Button>
              )}
              {["CLEARED", "CONFIRMED", "CLOSED"].includes(alert.status) && (
                <div className="p-3 bg-gray-50 rounded-lg text-center">
                  <CheckCircle className="h-5 w-5 text-emerald-500 mx-auto mb-1" />
                  <p className="text-[12px] text-gray-600 font-medium">Alert is closed</p>
                  <p className="text-[11px] text-gray-400">Outcome: {alert.status}</p>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>

      {/* Close Alert Modal */}
      {closingModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl border max-w-md w-full overflow-hidden animate-fade-in">
            <div className="px-6 py-4 border-b flex justify-between items-center bg-gray-50">
              <h3 className="font-semibold text-[15px] flex items-center gap-2">
                <Lock className="h-4 w-4 text-red-600" /> Close Fraud Alert
              </h3>
              <button onClick={() => setClosingModal(false)} className="text-gray-400 hover:text-gray-600">
                <X className="h-4 w-4" />
              </button>
            </div>
            <form onSubmit={handleCloseAlert}>
              <div className="p-6 space-y-4">
                <div className="space-y-1.5">
                  <label className="text-[12px] font-semibold text-gray-400">OUTCOME *</label>
                  <select
                    value={closeOutcome}
                    onChange={(e) => setCloseOutcome(e.target.value as typeof closeOutcome)}
                    className="w-full p-2.5 border rounded-lg text-[13px] focus:ring-1 focus:ring-blue-500 focus:outline-none"
                    required
                  >
                    <option value="CLEARED">CLEARED — No Fraud Found</option>
                    <option value="CONFIRMED">CONFIRMED — Fraud Confirmed</option>
                    <option value="INCONCLUSIVE">INCONCLUSIVE — Cannot Determine</option>
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="text-[12px] font-semibold text-gray-400">INVESTIGATION FINDINGS *</label>
                  <textarea
                    required
                    value={closeFindings}
                    onChange={(e) => setCloseFindings(e.target.value)}
                    placeholder="Summarise the investigation findings..."
                    className="w-full min-h-[80px] p-3 border rounded-lg text-[13px] focus:ring-1 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-[12px] font-semibold text-gray-400">COMPLIANCE ACTION (optional)</label>
                  <select
                    value={complianceAction}
                    onChange={(e) => setComplianceAction(e.target.value)}
                    className="w-full p-2.5 border rounded-lg text-[13px] focus:ring-1 focus:ring-blue-500 focus:outline-none"
                  >
                    <option value="">— No action taken —</option>
                    <option value="ACCOUNT_REVIEW">Account Review</option>
                    <option value="REFERRED_TO_POLICE">Referred to Police</option>
                    <option value="LOAN_SUSPENDED">Loan Suspended</option>
                    <option value="CLIENT_BLACKLISTED">Client Blacklisted</option>
                    <option value="NO_ACTION">No Action</option>
                  </select>
                </div>
                {complianceAction && (
                  <div className="space-y-1.5">
                    <label className="text-[12px] font-semibold text-gray-400">ACTION REASON</label>
                    <input
                      value={actionReason}
                      onChange={(e) => setActionReason(e.target.value)}
                      placeholder="Reason for this action..."
                      className="w-full p-2.5 border rounded-lg text-[13px] focus:ring-1 focus:ring-blue-500 focus:outline-none"
                    />
                  </div>
                )}
              </div>
              <div className="px-6 py-4 bg-gray-50 border-t flex justify-end gap-2">
                <Button variant="secondary" onClick={() => setClosingModal(false)}>Cancel</Button>
                <Button
                  variant="primary"
                  type="submit"
                  disabled={submitting}
                  className={closeOutcome === "CONFIRMED" ? "bg-red-600 hover:bg-red-700" : "bg-emerald-600 hover:bg-emerald-700"}
                >
                  {submitting ? "Saving..." : "Confirm & Close"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
