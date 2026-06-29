"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, Search, Calculator, ChevronRight, ChevronLeft, Check } from "lucide-react";
import Link from "next/link";
import useSWR from "swr";
import { fetcher, loansAPI, clientsAPI } from "@/lib/api";
import { loanApplicationSchema, type LoanApplicationFormData } from "@/lib/validations";
import { formatCurrency, calculateEMI } from "@/lib/utils";
import { useToast } from "@/components/ui/Toast";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";

const STEPS = ["Select Client", "Loan Details", "Cashflow"];
const PURPOSE_OPTIONS = [
  { value: "BUSINESS_EXPANSION", label: "Business Expansion" },
  { value: "WORKING_CAPITAL", label: "Working Capital" },
  { value: "EQUIPMENT_PURCHASE", label: "Equipment Purchase" },
  { value: "AGRICULTURE", label: "Agriculture" },
  { value: "EDUCATION", label: "Education" },
  { value: "MEDICAL", label: "Medical Emergency" },
  { value: "HOME_IMPROVEMENT", label: "Home Improvement" },
  { value: "DEBT_CONSOLIDATION", label: "Debt Consolidation" },
  { value: "OTHER", label: "Other" },
];

export default function NewLoanPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const toast = useToast();
  const [step, setStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedClient, setSelectedClient] = useState<Record<string,unknown> | null>(null);
  const [clientSearch, setClientSearch] = useState("");
  const [amount, setAmount] = useState(0);
  const [duration, setDuration] = useState(12);
  const [selectedProduct, setSelectedProduct] = useState<Record<string,unknown> | null>(null);

  const [cashflowData, setCashflowData] = useState({
    monthly_income: 0,
    other_income: 0,
    monthly_expenses: 0,
    existing_loan_payments: 0,
  });

  const handleCashflowChange = (field: string, val: string) => {
    setCashflowData((prev) => ({
      ...prev,
      [field]: Number(val) || 0,
    }));
  };

  const { data: products } = useSWR("/loans/products/", fetcher);
  const productList = products?.results || products || [];

  // Pre-select client from URL param
  const preClientId = searchParams.get("client");
  const { data: preClient } = useSWR(preClientId ? `/clients/${preClientId}/` : null, fetcher);
  useEffect(() => {
    if (preClient && !selectedClient) { setSelectedClient(preClient); setStep(1); }
  }, [preClient]); // eslint-disable-line

  const { data: clientResults } = useSWR(
    clientSearch.length >= 2 ? `/clients/?search=${clientSearch}` : null, fetcher
  );
  const clientList = clientResults?.results || clientResults || [];

  const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm<LoanApplicationFormData>({
    resolver: zodResolver(loanApplicationSchema),
    defaultValues: { requested_duration_months: 12 },
  });

  const watchedAmount = watch("requested_amount") || 0;
  const watchedDuration = watch("requested_duration_months") || 12;
  const watchedProduct = watch("loan_product");

  useEffect(() => {
    setAmount(watchedAmount);
    setDuration(watchedDuration);
    if (watchedProduct) {
      const prod = productList.find((p: Record<string,unknown>) => p.id === watchedProduct);
      setSelectedProduct(prod || null);
    }
  }, [watchedAmount, watchedDuration, watchedProduct, productList]);

  const emi = selectedProduct
    ? calculateEMI(amount, Number(selectedProduct.interest_rate), duration)
    : amount > 0 && duration > 0 ? amount / duration : 0;

  const onSubmit = async (data: LoanApplicationFormData) => {
    if (!selectedClient) return;
    setIsSubmitting(true);
    try {
      const payload = { ...data, client: selectedClient.id };
      const res = await loansAPI.createApplication(payload as Record<string,unknown>);
      const loanId = res.data.id;

      // Submit cashflow details
      try {
        await loansAPI.submitCashflow(loanId, {
          monthly_income: cashflowData.monthly_income,
          other_income: cashflowData.other_income,
          monthly_expenses: cashflowData.monthly_expenses,
          existing_loan_payments: cashflowData.existing_loan_payments,
          proposed_monthly_payment: emi,
          officer_assessment_notes: data.officer_notes || "",
        });
      } catch (err) {
        console.error("Failed to submit cashflow details:", err);
      }

      toast.success("Loan application created successfully!");
      router.push(`/loans/${loanId}`);
    } catch (e: unknown) {
      const err = e as { response?: { data?: Record<string,unknown> } };
      toast.error(JSON.stringify(err.response?.data) || "Failed to create application");
    } finally { setIsSubmitting(false); }
  };

  return (
    <div className="w-full max-w-4xl space-y-6 mx-auto">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <Link href="/loans"><Button variant="ghost" size="sm" icon={<ArrowLeft className="h-4 w-4" />}>Back</Button></Link>
        <div>
          <p className="text-[var(--text-muted)] text-sm">Complete the application for a loan request</p>
        </div>
      </div>

      {/* Step indicator */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        {STEPS.map((s, i) => (
          <div key={s} className="flex items-center flex-1 last:flex-none">
            <div className={`step-dot ${i < step ? "step-dot-completed" : i === step ? "step-dot-active" : "step-dot-inactive"}`}>
              {i < step ? <Check className="h-4 w-4" /> : i + 1}
            </div>
            <span className={`ml-2 text-[13px] font-medium hidden sm:block ${i === step ? "text-[var(--color-primary)]" : i < step ? "text-emerald-600" : "text-[var(--text-muted)]"}`}>{s}</span>
            {i < STEPS.length - 1 && <div className={`step-line mx-3 ${i < step ? "step-line-completed" : ""}`} />}
          </div>
        ))}
      </div>

      {/* Step 1: Select Client */}
      {step === 0 && (
        <Card title="Select Client" subtitle="Search and select the borrower">
          {selectedClient ? (
            <div className="space-y-4">
              <div className="flex items-center gap-4 p-4 rounded-xl bg-blue-50 border border-blue-200">
                <div className="w-12 h-12 rounded-xl gradient-primary flex items-center justify-center">
                  <span className="text-white text-lg font-bold">{String(selectedClient.first_name || "?")[0]}{String(selectedClient.last_name || "?")[0]}</span>
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-[var(--text-primary)]">{String(selectedClient.first_name)} {String(selectedClient.last_name)}</p>
                  <p className="text-[13px] text-[var(--text-muted)]">{String(selectedClient.client_number)} · NIC: {String(selectedClient.nic_number)}</p>
                </div>
                <Badge status={String(selectedClient.status || "ACTIVE")} />
                <button onClick={() => setSelectedClient(null)} className="text-[13px] text-blue-600 hover:underline">Change</button>
              </div>
              <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4 -mx-6 -mb-6 mt-6 flex items-center justify-end rounded-b-[20px]"> {/* FIX[BUG 11]: fixed footer attached to bottom */}
                <Button onClick={() => setStep(1)} icon={<ChevronRight className="h-4 w-4" />}>Continue with this Client</Button>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-muted)]" />
                <input type="text" placeholder="Search by name, NIC, or phone..." value={clientSearch}
                  onChange={(e) => setClientSearch(e.target.value)}
                  className="w-full pl-9 pr-4 py-2.5 border border-[var(--border-color)] rounded-xl outline-none focus:border-[var(--color-primary)] focus:ring-2 focus:ring-blue-100 text-[14px]" />
              </div>
              {clientList.length > 0 && (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {clientList.map((c: Record<string,unknown>) => (
                    <button key={String(c.id)} onClick={() => { setSelectedClient(c); setValue("client", Number(c.id)); }}
                      className="w-full flex items-center gap-3 p-3 rounded-xl border border-[var(--border-color)] hover:border-blue-300 hover:bg-blue-50 transition-all text-left">
                      <div className="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                        <span className="text-blue-700 text-[12px] font-bold">{String(c.first_name || "?")[0]}{String(c.last_name || "?")[0]}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-[14px] font-medium">{String(c.first_name)} {String(c.last_name)}</p>
                        <p className="text-[12px] text-[var(--text-muted)]">{String(c.client_number)} · {String(c.nic_number)}</p>
                      </div>
                      <Badge status={String(c.status || "PENDING")} className="text-[11px]" />
                    </button>
                  ))}
                </div>
              )}
              {clientSearch.length >= 2 && clientList.length === 0 && (
                <p className="text-center py-6 text-[var(--text-muted)] text-[13px]">No clients found. <Link href="/clients/new" className="text-blue-600 hover:underline">Register a new client?</Link></p>
              )}
            </div>
          )}
        </Card>
      )}

      {/* Step 2: Loan Details */}
      {step === 1 && (
        <form onSubmit={handleSubmit(() => setStep(2))}>
          <div className="space-y-6">
            <Card title="Loan Details">
              <div className="space-y-4">
                <Select label="Loan Product" options={productList.map((p: Record<string,unknown>) => ({ value: String(p.id), label: String(p.name) }))} placeholder="Select a loan product"
                  {...register("loan_product", { valueAsNumber: true })} />
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <Input label="Requested Amount (LKR) *" type="number" min={0} placeholder="0"
                      error={errors.requested_amount?.message} {...register("requested_amount", { valueAsNumber: true })} />
                    {selectedProduct && (
                      <p className="text-[11px] text-gray-400 mt-1">Range: {formatCurrency(Number(selectedProduct.min_amount))} – {formatCurrency(Number(selectedProduct.max_amount))}</p>
                    )}
                  </div>
                  <div>
                    <label className="form-label">Duration (Months) *</label>
                    <input type="range" min={1} max={120} value={watchedDuration}
                      {...register("requested_duration_months", { valueAsNumber: true })}
                      className="w-full mt-2" />
                    <p className="text-[13px] font-semibold text-[var(--text-primary)] mt-1">{watchedDuration} months ({Math.floor(watchedDuration / 12)}y {watchedDuration % 12}m)</p>
                    {errors.requested_duration_months && <p className="form-error">{errors.requested_duration_months.message}</p>}
                  </div>
                </div>
                <Select label="Loan Purpose *" options={PURPOSE_OPTIONS} placeholder="Select purpose"
                  error={errors.loan_purpose?.message} {...register("loan_purpose")} />
                <div>
                  <label className="form-label">Purpose Description</label>
                  <textarea rows={3} placeholder="Describe how the funds will be used..."
                    {...register("purpose_description")}
                    className="form-input resize-none" />
                </div>
              </div>
            </Card>

            {/* EMI Calculator */}
            {amount > 0 && duration > 0 && (
              <Card title="Estimated Monthly Installment">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-center">
                  <div className="p-4 rounded-xl bg-blue-50">
                    <p className="text-[12px] text-blue-600 mb-1">Principal</p>
                    <p className="text-lg font-bold text-blue-800">{formatCurrency(amount)}</p>
                  </div>
                  <div className="p-4 rounded-xl bg-emerald-50">
                    <p className="text-[12px] text-emerald-600 mb-1 flex items-center justify-center gap-1"><Calculator className="h-3 w-3" />Monthly EMI</p>
                    <p className="text-2xl font-bold text-emerald-800">{formatCurrency(emi)}</p>
                  </div>
                  <div className="p-4 rounded-xl bg-purple-50">
                    <p className="text-[12px] text-purple-600 mb-1">Interest Rate</p>
                    <p className="text-lg font-bold text-purple-800">{selectedProduct ? `${selectedProduct.interest_rate}% p.a.` : "—"}</p>
                  </div>
                </div>
              </Card>
            )}

            <div className="sticky bottom-0 bg-[var(--background)] border-t border-gray-200 py-4 mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between z-10"> {/* FIX[BUG 11]: fixed footer */}
              <Button type="button" variant="outline" onClick={() => setStep(0)} icon={<ChevronLeft className="h-4 w-4" />}>Back</Button>
              <Button type="submit" icon={<ChevronRight className="h-4 w-4" />}>Continue to Cashflow</Button>
            </div>
          </div>
        </form>
      )}

      {/* Step 3: Cashflow */}
      {step === 2 && (
        <form onSubmit={handleSubmit(onSubmit)}>
          <Card title="Cashflow Assessment" subtitle="Financial capacity assessment">
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Monthly Income (LKR)"
                  type="number"
                  min={0}
                  value={cashflowData.monthly_income || ""}
                  onChange={(e) => handleCashflowChange("monthly_income", e.target.value)}
                />
                <Input
                  label="Other Income (LKR)"
                  type="number"
                  min={0}
                  value={cashflowData.other_income || ""}
                  onChange={(e) => handleCashflowChange("other_income", e.target.value)}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Monthly Expenses (LKR)"
                  type="number"
                  min={0}
                  value={cashflowData.monthly_expenses || ""}
                  onChange={(e) => handleCashflowChange("monthly_expenses", e.target.value)}
                />
                <Input
                  label="Existing Loan Payments (LKR)"
                  type="number"
                  min={0}
                  value={cashflowData.existing_loan_payments || ""}
                  onChange={(e) => handleCashflowChange("existing_loan_payments", e.target.value)}
                />
              </div>
              <div>
                <label className="form-label">Officer Notes</label>
                <textarea
                  rows={3}
                  placeholder="Any additional notes about this application..."
                  {...register("officer_notes")}
                  className="form-input resize-none"
                />
              </div>
              <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4 -mx-6 -mb-6 mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between rounded-b-[20px]"> {/* FIX[BUG 11]: fixed footer */}
                <Button type="button" variant="outline" onClick={() => setStep(1)} icon={<ChevronLeft className="h-4 w-4" />}>Back</Button>
                <div className="flex gap-2">
                  <Button type="submit" variant="secondary" loading={isSubmitting}>Save as Draft</Button>
                  <Button type="submit" loading={isSubmitting}>Submit for Review</Button>
                </div>
              </div>
            </div>
          </Card>
        </form>
      )}
    </div>
  );
}
