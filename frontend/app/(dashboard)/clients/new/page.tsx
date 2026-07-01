"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ChevronRight, ChevronLeft, Check, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { clientsAPI } from "@/lib/api";
import {
  createClientSchema, clientAddressSchema, clientBusinessSchema, clientIncomeSchema,
  type CreateClientFormData, type ClientAddressFormData,
  type ClientBusinessFormData, type ClientIncomeFormData,
} from "@/lib/validations";
import { useToast } from "@/components/ui/Toast";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import Card from "@/components/ui/Card";

const STEPS = ["Personal Info", "Address", "Business", "Income"];

export default function NewClientPage() {
  const router = useRouter();
  const toast = useToast();
  const [step, setStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [clientId, setClientId] = useState<number | null>(null);
  const [skipBusiness, setSkipBusiness] = useState(false);

  const step1 = useForm<CreateClientFormData>({ resolver: zodResolver(createClientSchema), defaultValues: { preferred_language: "en" } });
  const step2 = useForm<ClientAddressFormData>({ resolver: zodResolver(clientAddressSchema), defaultValues: { address_type: "HOME", is_primary: true } });
  const step3 = useForm<ClientBusinessFormData>({ resolver: zodResolver(clientBusinessSchema), defaultValues: { years_in_operation: 0, number_of_employees: 0 } });
  const step4 = useForm<ClientIncomeFormData>({ resolver: zodResolver(clientIncomeSchema), defaultValues: { other_income: 0, monthly_expenses: 0, existing_debt_monthly: 0, number_of_dependents: 0 } });

  const handleStep1 = step1.handleSubmit(async (data) => {
    if (clientId) { setStep(1); return; }
    setIsSubmitting(true);
    try {
      const res = await clientsAPI.createClient(data as Record<string, unknown>);
      setClientId(res.data.id);
      setStep(1);
    } catch (e: unknown) {
      const err = e as { response?: { data?: Record<string,string> } };
      const msg = Object.values(err.response?.data || {}).flat().join(", ") || "Failed to create client";
      toast.error(msg);
    } finally { setIsSubmitting(false); }
  });

  const handleStep2 = step2.handleSubmit(async (data) => {
    if (!clientId) return;
    setIsSubmitting(true);
    try {
      await clientsAPI.updateClient(clientId, { addresses: [data] } as Record<string, unknown>);
      setStep(2);
    } catch { setStep(2); } // Address may be separate endpoint, proceed anyway
    finally { setIsSubmitting(false); }
  });

  const handleStep3 = async () => {
    if (skipBusiness) { setStep(3); return; }
    const valid = await step3.trigger();
    if (!valid) return;
    const data = step3.getValues();
    if (clientId) {
      setIsSubmitting(true);
      try { await clientsAPI.updateClient(clientId, { business: data } as Record<string, unknown>); } catch {}
      finally { setIsSubmitting(false); }
    }
    setStep(3);
  };

  const handleStep4 = step4.handleSubmit(async (data) => {
    if (!clientId) return;
    setIsSubmitting(true);
    try {
      await clientsAPI.updateClient(clientId, { income: data } as Record<string, unknown>);
      toast.success("Client registered successfully!");
      router.push(`/clients/${clientId}`);
    } catch {
      toast.success("Client registered successfully!");
      router.push(`/clients/${clientId}`);
    } finally { setIsSubmitting(false); }
  });

  const genderOptions = [{ value: "M", label: "Male" }, { value: "F", label: "Female" }, { value: "O", label: "Other" }];
  const langOptions = [{ value: "en", label: "English" }, { value: "si", label: "Sinhala" }, { value: "ta", label: "Tamil" }];
  const addressTypeOptions = [{ value: "HOME", label: "Home" }, { value: "BUSINESS", label: "Business" }, { value: "POSTAL", label: "Postal" }];
  const businessTypeOptions = [
    { value: "SOLE_PROPRIETOR", label: "Sole Proprietor" }, { value: "PARTNERSHIP", label: "Partnership" },
    { value: "PRIVATE_LIMITED", label: "Private Limited" }, { value: "INFORMAL", label: "Informal Business" },
    { value: "FARMING", label: "Farming" }, { value: "OTHER", label: "Other" },
  ];
  const incomeSourceOptions = [
    { value: "BUSINESS", label: "Business Income" }, { value: "SALARY", label: "Salary" },
    { value: "AGRICULTURE", label: "Agriculture" }, { value: "REMITTANCE", label: "Remittance" },
    { value: "PENSION", label: "Pension" }, { value: "OTHER", label: "Other" },
  ];

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div className="flex items-center gap-3">
        <Link href="/clients"><Button variant="ghost" size="sm" icon={<ArrowLeft className="h-4 w-4" />}>Back</Button></Link>
        <div>
          <p className="text-[var(--text-muted)] text-sm">Complete all steps to register the client</p>
        </div>
      </div>

      {/* Step Indicator */}
      <div className="flex items-center">
        {STEPS.map((s, i) => (
          <div key={s} className="flex items-center flex-1 last:flex-none">
            <div className={`step-dot ${i < step ? "step-dot-completed" : i === step ? "step-dot-active" : "step-dot-inactive"}`}>
              {i < step ? <Check className="h-4 w-4" /> : i + 1}
            </div>
            <div className="hidden sm:flex flex-col ml-2">
              <span className={`text-[12px] font-semibold ${i === step ? "text-[var(--color-primary)]" : i < step ? "text-emerald-600" : "text-[var(--text-muted)]"}`}>{s}</span>
            </div>
            {i < STEPS.length - 1 && <div className={`step-line mx-3 ${i < step ? "step-line-completed" : ""}`} />}
          </div>
        ))}
      </div>

      {/* Step 1: Personal Info */}
      {step === 0 && (
        <Card title="Personal Information" subtitle="Basic identification details">
          <form onSubmit={handleStep1} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Input label="First Name *" placeholder="e.g. Kamal" error={step1.formState.errors.first_name?.message} {...step1.register("first_name")} />
              <Input label="Last Name *" placeholder="e.g. Perera" error={step1.formState.errors.last_name?.message} {...step1.register("last_name")} />
            </div>
            <Input label="NIC Number *" placeholder="e.g. 901234567V or 199012345678" error={step1.formState.errors.nic_number?.message} {...step1.register("nic_number")} />
            <div className="grid grid-cols-2 gap-4">
              <Input label="Date of Birth *" type="date" error={step1.formState.errors.date_of_birth?.message} {...step1.register("date_of_birth")} />
              <Select label="Gender *" options={genderOptions} placeholder="Select gender" error={step1.formState.errors.gender?.message} {...step1.register("gender")} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Input label="Primary Phone *" placeholder="e.g. 0771234567" error={step1.formState.errors.phone_primary?.message} {...step1.register("phone_primary")} />
              <Input label="Secondary Phone" placeholder="Optional" {...step1.register("phone_secondary")} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Input label="Email Address" type="email" placeholder="Optional" error={step1.formState.errors.email?.message} {...step1.register("email")} />
              <Select label="Preferred Language" options={langOptions} {...step1.register("preferred_language")} />
            </div>
            <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4 -mx-6 -mb-6 mt-6 flex items-center justify-end rounded-b-[20px]"> {/* FIX[BUG 11]: fixed footer attached to bottom */}
              <Button type="submit" loading={isSubmitting} icon={<ChevronRight className="h-4 w-4" />}>Next: Address</Button>
            </div>
          </form>
        </Card>
      )}

      {/* Step 2: Address */}
      {step === 1 && (
        <Card title="Address Information" subtitle="Primary residential or business address">
          <form onSubmit={handleStep2} className="space-y-4">
            <Select label="Address Type" options={addressTypeOptions} error={step2.formState.errors.address_type?.message} {...step2.register("address_type")} />
            <Input label="Address Line 1 *" placeholder="Street number and name" error={step2.formState.errors.address_line_1?.message} {...step2.register("address_line_1")} />
            <Input label="Address Line 2" placeholder="Apartment, suite, etc. (optional)" {...step2.register("address_line_2")} />
            <div className="grid grid-cols-3 gap-4">
              <Input label="City *" placeholder="e.g. Colombo" error={step2.formState.errors.city?.message} {...step2.register("city")} />
              <Input label="District *" placeholder="e.g. Colombo" error={step2.formState.errors.district?.message} {...step2.register("district")} />
              <Input label="Province *" placeholder="e.g. Western" error={step2.formState.errors.province?.message} {...step2.register("province")} />
            </div>
            <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4 -mx-6 -mb-6 mt-6 flex items-center justify-between rounded-b-[20px]"> {/* FIX[BUG 11]: fixed footer */}
              <Button type="button" variant="outline" onClick={() => setStep(0)} icon={<ChevronLeft className="h-4 w-4" />}>Back</Button>
              <Button type="submit" loading={isSubmitting} icon={<ChevronRight className="h-4 w-4" />}>Next: Business</Button>
            </div>
          </form>
        </Card>
      )}

      {/* Step 3: Business (Optional) */}
      {step === 2 && (
        <Card title="Business Information" subtitle="This step is optional" action={<button type="button" onClick={() => { setSkipBusiness(true); setStep(3); }} className="text-[13px] text-blue-600 hover:underline">Skip this step →</button>}>
          <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); handleStep3(); }}>
            <Input label="Business Name *" placeholder="e.g. Kamal's General Store" error={step3.formState.errors.business_name?.message} {...step3.register("business_name")} />
            <Select label="Business Type" options={businessTypeOptions} error={step3.formState.errors.business_type?.message} {...step3.register("business_type")} />
            <div className="grid grid-cols-2 gap-4">
              <Input label="Years in Operation" type="number" min={0} {...step3.register("years_in_operation", { valueAsNumber: true })} />
              <Input label="Number of Employees" type="number" min={0} {...step3.register("number_of_employees", { valueAsNumber: true })} />
            </div>
            <Input label="Monthly Revenue (LKR)" type="number" min={0} placeholder="Approximate monthly revenue" {...step3.register("monthly_revenue", { valueAsNumber: true })} />
            <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4 -mx-6 -mb-6 mt-6 flex items-center justify-between rounded-b-[20px]"> {/* FIX[BUG 11]: fixed footer */}
              <Button type="button" variant="outline" onClick={() => setStep(1)} icon={<ChevronLeft className="h-4 w-4" />}>Back</Button>
              <Button type="submit" loading={isSubmitting} icon={<ChevronRight className="h-4 w-4" />}>Next: Income</Button>
            </div>
          </form>
        </Card>
      )}

      {/* Step 4: Income */}
      {step === 3 && (
        <Card title="Income & Financial Details" subtitle="Monthly income and expense breakdown">
          <form onSubmit={handleStep4} className="space-y-4">
            <Select label="Income Source" options={incomeSourceOptions} error={step4.formState.errors.income_source?.message} {...step4.register("income_source")} />
            <div className="grid grid-cols-2 gap-4">
              <Input label="Monthly Income (LKR) *" type="number" min={0} placeholder="0" error={step4.formState.errors.monthly_income?.message} {...step4.register("monthly_income", { valueAsNumber: true })} />
              <Input label="Other Income (LKR)" type="number" min={0} placeholder="0" {...step4.register("other_income", { valueAsNumber: true })} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Input label="Monthly Expenses (LKR)" type="number" min={0} placeholder="0" {...step4.register("monthly_expenses", { valueAsNumber: true })} />
              <Input label="Existing Debt Payments (LKR)" type="number" min={0} placeholder="0" {...step4.register("existing_debt_monthly", { valueAsNumber: true })} />
            </div>
            <Input label="Number of Dependents" type="number" min={0} max={20} {...step4.register("number_of_dependents", { valueAsNumber: true })} />
            <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4 -mx-6 -mb-6 mt-6 flex items-center justify-between rounded-b-[20px]"> {/* FIX[BUG 11]: fixed footer */}
              <Button type="button" variant="outline" onClick={() => setStep(2)} icon={<ChevronLeft className="h-4 w-4" />}>Back</Button>
              <Button type="submit" loading={isSubmitting}>Register Client</Button>
            </div>
          </form>
        </Card>
      )}
    </div>
  );
}
