"use client";

import Link from "next/link";
import useSWR from "swr";
import { ArrowLeft, FileText, Shield, Brain, CheckCircle, XCircle, Clock, AlertTriangle } from "lucide-react";
import { fetcher } from "@/lib/api";
import { formatCurrency, formatDate, formatRelativeTime } from "@/lib/utils";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import StatCard from "@/components/ui/StatCard";
import Spinner from "@/components/ui/Spinner";
import Modal from "@/components/ui/Modal";
import { usePermissions } from "@/lib/permissions";
import { useState, use } from "react";
import { useToast } from "@/components/ui/Toast";
import { approvalsAPI } from "@/lib/api";
import api from "@/lib/api";

export default function LoanDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { can, role } = usePermissions();
  const toast = useToast();
  const [actionComments, setActionComments] = useState("");
  const [isActioning, setIsActioning] = useState(false);

  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [uploadType, setUploadType] = useState("APPLICATION_FORM");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  
  const resolvedParams = use(params);
  const id = resolvedParams.id;

  const { data: loan, isLoading, mutate } = useSWR(`/loans/applications/${id}/`, fetcher);

  if (isLoading) return <div className="flex items-center justify-center h-64"><Spinner size="lg" /></div>;
  if (!loan) return <div className="text-center py-16"><p className="text-[var(--text-muted)]">Application not found</p><Link href="/loans" className="btn btn-outline mt-4">Back to Loans</Link></div>;

  const riskAssessment = loan.risk_assessment;
  const aiRec = loan.ai_recommendation;
  const cashflow = loan.cashflow;

  const statusTimeline = [
    { key: "DRAFT", label: "Draft" },
    { key: "SUBMITTED", label: "Submitted" },
    { key: "AI_SCREENING", label: "AI Screening" },
    { key: "RISK_REVIEWED", label: "Risk Reviewed" },
    { key: "MANAGER_REVIEW", label: "Manager Review" },
    { key: "APPROVED", label: "Approved" },
    { key: "DISBURSED", label: "Disbursed" },
  ];

  const currentIdx = statusTimeline.findIndex(s => s.key === loan.status);
  const isRejected = loan.status === "REJECTED" || loan.status === "CANCELLED";

  const handleAction = async (decision: string) => {
    if (!actionComments.trim()) { toast.warning("Please add comments before making a decision"); return; }
    setIsActioning(true);
    try {
      await approvalsAPI.makeDecision(Number(id), { decision, comments: actionComments });
      toast.success(`Application ${decision.toLowerCase()} successfully`);
      mutate();
      setActionComments("");
    } catch { toast.error("Failed to submit decision"); }
    finally { setIsActioning(false); }
  };

  const handleSubmitReview = async () => {
    setIsActioning(true);
    try {
      await api.post(`/loans/applications/${id}/submit/`);
      toast.success("Application submitted for review successfully");
      mutate();
    } catch (error) {
      toast.error("Failed to submit application");
    } finally {
      setIsActioning(false);
    }
  };

  const handleTriggerAI = async () => {
    setIsActioning(true);
    try {
      toast.info("Running AI Risk Assessment...");
      await api.post(`/loans/applications/${id}/risk-assess/`);
      toast.info("Running AI Recommendation...");
      await api.post(`/loans/applications/${id}/recommend/`);
      toast.success("AI Processing completed");
      mutate();
    } catch (error) {
      toast.error("Failed during AI processing");
    } finally {
      setIsActioning(false);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append("document_type", uploadType);
    formData.append("file", uploadFile);

    try {
      await api.post(`/loans/applications/${id}/documents/`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      toast.success("Document uploaded successfully");
      setIsUploadModalOpen(false);
      setUploadFile(null);
      mutate();
    } catch (error) {
      toast.error("Failed to upload document");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Link href="/loans" className="btn btn-ghost btn-sm">
        <ArrowLeft className="h-4 w-4 mr-1.5" />
        All Applications
      </Link>

      {/* Header */}
      <div className="card p-6">
        <div className="flex flex-col md:flex-row items-start gap-4">
          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-3 mb-2">
              <Badge status={loan.status} />
            </div>
            <div className="flex flex-wrap gap-4 text-[13px] text-[var(--text-muted)]">
              <span>Client: <Link href={`/clients/${loan.client?.id || loan.client}`} className="text-blue-600 hover:underline font-medium">{loan.client?.first_name} {loan.client?.last_name}</Link></span>
              <span>Amount: <span className="font-semibold text-[var(--text-primary)]">{formatCurrency(loan.requested_amount)}</span></span>
              <span>Duration: {loan.requested_duration_months} months</span>
              <span>Applied: {formatDate(loan.created_at)}</span>
            </div>
          </div>
        </div>

        {/* Status Timeline */}
        {!isRejected && (
          <div className="mt-6 flex items-center">
            {statusTimeline.map((s, i) => (
              <div key={s.key} className="flex items-center flex-1 last:flex-none">
                <div className={`w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-bold flex-shrink-0 ${i <= currentIdx ? "bg-emerald-500 text-white" : "bg-gray-200 text-gray-500"}`}>
                  {i <= currentIdx ? <CheckCircle className="h-4 w-4" /> : i + 1}
                </div>
                <span className={`ml-1.5 text-[11px] font-medium hidden lg:block ${i <= currentIdx ? "text-emerald-700" : "text-gray-400"}`}>{s.label}</span>
                {i < statusTimeline.length - 1 && <div className={`flex-1 h-0.5 mx-2 ${i < currentIdx ? "bg-emerald-400" : "bg-gray-200"}`} />}
              </div>
            ))}
          </div>
        )}
        {isRejected && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-xl flex items-center gap-2">
            <XCircle className="h-5 w-5 text-red-600" />
            <span className="text-[13px] font-medium text-red-700">This application has been {loan.status.toLowerCase()}</span>
          </div>
        )}
      </div>

      {/* Content Grid */}
      <div className={`grid grid-cols-1 gap-6 ${(aiRec || riskAssessment) ? 'lg:grid-cols-3' : 'lg:grid-cols-2'}`}>
        {/* Left Column */}
        <div className="space-y-6">
          <Card title="Application Details">
            <dl className="space-y-2.5">
              {[
                ["Application #", loan.application_number],
                ["Client", `${loan.client?.first_name || ""} ${loan.client?.last_name || ""}`],
                ["Product", loan.loan_product?.name || "—"],
                ["Amount", formatCurrency(loan.requested_amount)],
                ["Duration", `${loan.requested_duration_months} months`],
                ["Purpose", loan.loan_purpose?.replace(/_/g, " ") || "—"],
                ["Description", loan.purpose_description || "—"],
                ["Created By", loan.created_by?.username || "—"],
              ].map(([label, value]) => (
                <div key={label} className="flex justify-between py-1 border-b border-gray-50 last:border-0">
                  <dt className="text-[12px] text-[var(--text-muted)]">{label}</dt>
                  <dd className="text-[13px] font-medium text-[var(--text-primary)] text-right max-w-[55%]">{value}</dd>
                </div>
              ))}
            </dl>
          </Card>

          {/* Documents */}
          <Card title="Documents" action={can("loans:write") && <Button size="sm" variant="outline" onClick={() => setIsUploadModalOpen(true)}>Upload</Button>}>
            {loan.documents?.length > 0 ? (
              <div className="space-y-2">
                {loan.documents.map((d: Record<string,unknown>, i: number) => (
                  <div key={i} className="flex items-center gap-3 p-2 rounded-lg border border-[var(--border-color)]">
                    <FileText className="h-4 w-4 text-blue-600" />
                    <div className="flex-1 min-w-0">
                      <p className="text-[13px] font-medium truncate">{String(d.file_name || d.document_type)}</p>
                      <p className="text-[11px] text-gray-400">{formatRelativeTime(String(d.uploaded_at || new Date()))}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-[13px] text-[var(--text-muted)] text-center py-4">No documents uploaded yet</p>
            )}
          </Card>

          {/* Officer Notes */}
          {loan.officer_notes && (
            <Card title="Officer Notes">
              <p className="text-[13px] text-[var(--text-primary)] leading-relaxed">{loan.officer_notes}</p>
            </Card>
          )}
        </div>

        {/* Middle Column */}
        {(aiRec || riskAssessment) && (
          <div className="space-y-6">
          {aiRec && (
            <Card title="AI Recommendation" subtitle="Powered by MicroFinance AI Engine">
              <div className="space-y-4">
                <div className={`p-4 rounded-xl border-2 ${aiRec.recommendation_type?.includes("APPROVAL") ? "border-emerald-300 bg-emerald-50" : aiRec.recommendation_type?.includes("REJECTION") ? "border-red-300 bg-red-50" : "border-amber-300 bg-amber-50"}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <Brain className="h-5 w-5" />
                    <Badge status={aiRec.recommendation_type || "PENDING"} />
                  </div>
                  <p className="text-[13px] font-medium">{aiRec.explanation || "No explanation provided."}</p>
                  {aiRec.recommended_amount && (
                    <p className="text-[12px] mt-2 text-[var(--text-muted)]">Recommended Amount: {formatCurrency(aiRec.recommended_amount)}</p>
                  )}
                </div>
                {/* Confidence gauge */}
                {aiRec.confidence != null && (
                  <div>
                    <div className="flex justify-between mb-1"><span className="text-[12px] text-[var(--text-muted)]">Confidence</span><span className="text-[13px] font-bold">{(aiRec.confidence * 100).toFixed(0)}%</span></div>
                    <div className="progress-bar"><div className="progress-bar-fill bg-blue-500" style={{ width: `${aiRec.confidence * 100}%` }} /></div>
                  </div>
                )}
                {aiRec.reasons?.length > 0 && (
                  <div>
                    <p className="text-[12px] font-semibold text-[var(--text-muted)] mb-2">Key Factors</p>
                    <ul className="space-y-1">
                      {aiRec.reasons.map((r: string, i: number) => (
                        <li key={i} className="text-[13px] text-[var(--text-primary)] flex items-start gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-blue-400 mt-1.5 flex-shrink-0" />
                          {r}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </Card>
          )}

          {riskAssessment && (
            <Card title="Risk Assessment">
              <div className="space-y-4">
                <div className="flex items-center gap-4">
                  <div className={`w-20 h-20 rounded-xl flex flex-col items-center justify-center ${riskAssessment.risk_category === "LOW" ? "bg-emerald-50" : riskAssessment.risk_category === "MEDIUM" ? "bg-amber-50" : "bg-red-50"}`}>
                    <p className={`text-2xl font-bold ${riskAssessment.risk_category === "LOW" ? "text-emerald-700" : riskAssessment.risk_category === "MEDIUM" ? "text-amber-700" : "text-red-700"}`}>{Number(riskAssessment.risk_score).toFixed(0)}</p>
                    <p className="text-[10px] font-semibold opacity-75">Score</p>
                  </div>
                  <div>
                    <Badge status={riskAssessment.risk_category} />
                    <p className="text-[12px] text-[var(--text-muted)] mt-1">{riskAssessment.ai_rationale?.slice(0, 100) || "Risk assessment completed."}</p>
                  </div>
                </div>
                {/* Factor breakdown */}
                <div className="space-y-2">
                  {[
                    { label: "DTI Score", val: riskAssessment.dti_score },
                    { label: "LTI Score", val: riskAssessment.lti_score },
                    { label: "KYC Score", val: riskAssessment.kyc_score },
                    { label: "Income Stability", val: riskAssessment.income_stability_score },
                    { label: "Repayment History", val: riskAssessment.repayment_history_score },
                  ].filter(f => f.val != null).map((f) => (
                    <div key={f.label}>
                      <div className="flex justify-between mb-0.5"><span className="text-[12px] text-[var(--text-muted)]">{f.label}</span><span className="text-[12px] font-semibold">{Number(f.val).toFixed(0)}</span></div>
                      <div className="progress-bar"><div className={`progress-bar-fill ${Number(f.val) >= 70 ? "bg-emerald-500" : Number(f.val) >= 40 ? "bg-amber-500" : "bg-red-500"}`} style={{ width: `${f.val}%` }} /></div>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          )}
        </div>
        )}

        {/* Right Column — Actions */}
        <div className="space-y-6">
          <Card title="Actions">
            <div className="space-y-4">
              {/* Role-based actions */}
              {(role === "loan_officer" || role === "admin") && loan.status === "DRAFT" && (
                <Button className="w-full" icon={<FileText className="h-4 w-4" />} onClick={handleSubmitReview} loading={isActioning}>Submit for Review</Button>
              )}

              {(role === "risk_analyst" || role === "admin") && loan.status === "AI_SCREENING" && !riskAssessment && (
                <Button className="w-full" variant="primary" icon={<Brain className="h-4 w-4" />} onClick={handleTriggerAI} loading={isActioning}>Run AI Assessment</Button>
              )}

              {(role === "risk_analyst" || role === "admin") && (loan.status === "AI_SCREENING" || loan.status === "RISK_REVIEWED") && riskAssessment && (
                <div className="space-y-3">
                  <p className="text-[13px] font-semibold text-[var(--text-primary)]">Risk Analyst Review</p>
                  <textarea rows={3} placeholder="Enter your review notes..." value={actionComments} onChange={(e) => setActionComments(e.target.value)} className="form-input resize-none text-[13px]" />
                  <div className="grid grid-cols-2 gap-2">
                    <Button variant="primary" size="sm" loading={isActioning} onClick={() => handleAction("APPROVED")} icon={<CheckCircle className="h-4 w-4" />}>Approve</Button>
                    <Button variant="danger" size="sm" loading={isActioning} onClick={() => handleAction("REJECTED")} icon={<XCircle className="h-4 w-4" />}>Reject</Button>
                  </div>
                  <Button variant="outline" size="sm" className="w-full" loading={isActioning} onClick={() => handleAction("ESCALATE")}>Escalate to Manager</Button>
                </div>
              )}

              {(role === "branch_manager" || role === "admin") && loan.status === "MANAGER_REVIEW" && (
                <div className="space-y-3">
                  <p className="text-[13px] font-semibold text-[var(--text-primary)]">Branch Manager Decision</p>
                  <textarea rows={3} placeholder="Decision comments..." value={actionComments} onChange={(e) => setActionComments(e.target.value)} className="form-input resize-none text-[13px]" />
                  <div className="grid grid-cols-2 gap-2">
                    <Button variant="primary" size="sm" loading={isActioning} onClick={() => handleAction("APPROVED")} icon={<CheckCircle className="h-4 w-4" />}>Approve</Button>
                    <Button variant="danger" size="sm" loading={isActioning} onClick={() => handleAction("REJECTED")} icon={<XCircle className="h-4 w-4" />}>Reject</Button>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <Button variant="outline" size="sm" loading={isActioning} onClick={() => handleAction("MORE_INFO")}>More Info</Button>
                    <Button variant="outline" size="sm" loading={isActioning} onClick={() => handleAction("ESCALATE")}>To Committee</Button>
                  </div>
                </div>
              )}

              {(role === "credit_committee" || role === "admin") && loan.status === "COMMITTEE_REVIEW" && (
                <div className="space-y-3">
                  <p className="text-[13px] font-semibold">Committee Vote</p>
                  <textarea rows={3} placeholder="Your vote comments..." value={actionComments} onChange={(e) => setActionComments(e.target.value)} className="form-input resize-none text-[13px]" />
                  <div className="grid grid-cols-2 gap-2">
                    <Button variant="primary" size="sm" loading={isActioning} onClick={() => handleAction("APPROVED")} icon={<CheckCircle className="h-4 w-4" />}>Vote For</Button>
                    <Button variant="danger" size="sm" loading={isActioning} onClick={() => handleAction("REJECTED")} icon={<XCircle className="h-4 w-4" />}>Vote Against</Button>
                  </div>
                </div>
              )}

              {(role === "finance_staff" || role === "admin") && loan.status === "APPROVED" && (
                <Button className="w-full" variant="primary" icon={<CheckCircle className="h-4 w-4" />}>Process Disbursement</Button>
              )}

              {!["DRAFT", "AI_SCREENING", "RISK_REVIEWED", "MANAGER_REVIEW", "COMMITTEE_REVIEW", "APPROVED"].includes(loan.status) && (
                <p className="text-[13px] text-[var(--text-muted)] text-center py-4">No actions available for this status</p>
              )}
            </div>
          </Card>

          {cashflow && (
            <Card title="Cashflow Summary">
              <dl className="space-y-2.5">
                {[
                  ["Monthly Income", formatCurrency(cashflow.monthly_income)],
                  ["Other Income", formatCurrency(cashflow.other_income)],
                  ["Monthly Expenses", formatCurrency(cashflow.monthly_expenses)],
                  ["Existing Debt", formatCurrency(cashflow.existing_loan_payments)],
                  ["Proposed Payment", formatCurrency(cashflow.proposed_monthly_payment)],
                  ["Net Cashflow", formatCurrency(cashflow.net_cashflow)],
                ].map(([label, value]) => (
                  <div key={label} className="flex justify-between py-1 border-b border-gray-50 last:border-0">
                    <dt className="text-[12px] text-[var(--text-muted)]">{label}</dt>
                    <dd className="text-[13px] font-medium">{value}</dd>
                  </div>
                ))}
              </dl>
              {cashflow.debt_to_income_ratio != null && (
                <div className={`mt-3 p-3 rounded-lg ${cashflow.debt_to_income_ratio < 0.35 ? "bg-emerald-50 border border-emerald-200" : cashflow.debt_to_income_ratio < 0.5 ? "bg-amber-50 border border-amber-200" : "bg-red-50 border border-red-200"}`}>
                  <p className="text-[12px] font-semibold">Debt-to-Income Ratio</p>
                  <p className="text-2xl font-bold mt-0.5">{(cashflow.debt_to_income_ratio * 100).toFixed(1)}%</p>
                  <p className="text-[11px] opacity-75 mt-0.5">{cashflow.debt_to_income_ratio < 0.35 ? "Healthy — Within acceptable range" : cashflow.debt_to_income_ratio < 0.5 ? "Moderate — Requires attention" : "High — Elevated risk"}</p>
                </div>
              )}
            </Card>
          )}
        </div>
      </div>

      <Modal isOpen={isUploadModalOpen} onClose={() => !isUploading && setIsUploadModalOpen(false)} title="Upload Loan Document">
        <form onSubmit={handleUpload} className="space-y-4">
          <div>
            <label className="form-label">Document Type</label>
            <select
              value={uploadType}
              onChange={(e) => setUploadType(e.target.value)}
              className="form-input px-3"
              disabled={isUploading}
            >
              <option value="APPLICATION_FORM">Application Form</option>
              <option value="BUSINESS_PLAN">Business Plan</option>
              <option value="BANK_STATEMENT">Bank Statement</option>
              <option value="COLLATERAL_DOC">Collateral Document</option>
              <option value="GUARANTOR_DOC">Guarantor Document</option>
              <option value="OTHER">Other</option>
            </select>
          </div>
          <div>
            <label className="form-label">File</label>
            <input
              type="file"
              onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
              className="form-input px-3 py-2"
              required
              disabled={isUploading}
            />
          </div>
          <div className="pt-2 flex gap-3">
            <Button type="button" variant="outline" className="flex-1" onClick={() => setIsUploadModalOpen(false)} disabled={isUploading}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" className="flex-1" loading={isUploading}>
              Upload
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
