"use client";

import { useState, use, useEffect } from "react";
import Link from "next/link";
import useSWR from "swr";
import { ArrowLeft, FileText, Briefcase, DollarSign, Shield, Plus, Camera } from "lucide-react";
import api, { fetcher, clientsAPI } from "@/lib/api";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import { formatDate, formatCurrency, getInitials } from "@/lib/utils";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import StatCard from "@/components/ui/StatCard";
import Table from "@/components/ui/Table";
import Modal from "@/components/ui/Modal";
import { usePermissions } from "@/lib/permissions";
import { useToast } from "@/components/ui/Toast";

const TABS = ["Overview", "KYC", "Loan History", "Activity"];

export default function ClientDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { can } = usePermissions();
  const toast = useToast();
  const [activeTab, setActiveTab] = useState("Overview");
  
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [uploadType, setUploadType] = useState("NIC");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [modalTab, setModalTab] = useState("personal");
  const [isSaving, setIsSaving] = useState(false);

  // Personal Info States
  const [editFirstName, setEditFirstName] = useState("");
  const [editLastName, setEditLastName] = useState("");
  const [editNicNumber, setEditNicNumber] = useState("");
  const [editDob, setEditDob] = useState("");
  const [editGender, setEditGender] = useState("");
  const [editPhonePrimary, setEditPhonePrimary] = useState("");
  const [editPhoneSecondary, setEditPhoneSecondary] = useState("");
  const [editEmail, setEditEmail] = useState("");
  const [editLang, setEditLang] = useState("");

  // Address States
  const [editAddressType, setEditAddressType] = useState("HOME");
  const [editAddressLine1, setEditAddressLine1] = useState("");
  const [editAddressLine2, setEditAddressLine2] = useState("");
  const [editCity, setEditCity] = useState("");
  const [editDistrict, setEditDistrict] = useState("");
  const [editProvince, setEditProvince] = useState("");

  // Business States
  const [editBusinessName, setEditBusinessName] = useState("");
  const [editBusinessType, setEditBusinessType] = useState("SOLE_PROPRIETOR");
  const [editBusinessYears, setEditBusinessYears] = useState(0);
  const [editBusinessEmployees, setEditBusinessEmployees] = useState(0);
  const [editBusinessRevenue, setEditBusinessRevenue] = useState(0);

  // Income States
  const [editIncomeSource, setEditIncomeSource] = useState("BUSINESS");
  const [editMonthlyIncome, setEditMonthlyIncome] = useState(0);
  const [editOtherIncome, setEditOtherIncome] = useState(0);
  const [editMonthlyExpenses, setEditMonthlyExpenses] = useState(0);
  const [editExistingDebt, setEditExistingDebt] = useState(0);
  const [editDependents, setEditDependents] = useState(0);

  const openEditModal = () => {
    if (!client) return;
    
    // Personal Info
    setEditFirstName(client.first_name || "");
    setEditLastName(client.last_name || "");
    setEditNicNumber(client.nic_number || "");
    setEditDob(client.date_of_birth || "");
    setEditGender(client.gender || "M");
    setEditPhonePrimary(client.phone_primary || "");
    setEditPhoneSecondary(client.phone_secondary || "");
    setEditEmail(client.email || "");
    setEditLang(client.preferred_language || "en");

    // Address Info (take primary address if available)
    const primaryAddr = client.addresses?.find((a: Record<string,unknown>) => a.is_primary) || client.addresses?.[0] || {};
    setEditAddressType(primaryAddr.address_type || "HOME");
    setEditAddressLine1(primaryAddr.address_line_1 || "");
    setEditAddressLine2(primaryAddr.address_line_2 || "");
    setEditCity(primaryAddr.city || "");
    setEditDistrict(primaryAddr.district || "");
    setEditProvince(primaryAddr.province || "");

    // Business Info
    const biz = client.business || {};
    setEditBusinessName(biz.business_name || "");
    setEditBusinessType(biz.business_type || "SOLE_PROPRIETOR");
    setEditBusinessYears(biz.years_in_operation || 0);
    setEditBusinessEmployees(biz.number_of_employees || 0);
    setEditBusinessRevenue(biz.monthly_revenue || 0);

    // Income Info
    const inc = client.income || {};
    setEditIncomeSource(inc.income_source || "BUSINESS");
    setEditMonthlyIncome(inc.monthly_income || 0);
    setEditOtherIncome(inc.other_income || 0);
    setEditMonthlyExpenses(inc.monthly_expenses || 0);
    setEditExistingDebt(inc.existing_debt_monthly || 0);
    setEditDependents(inc.number_of_dependents || 0);

    setModalTab("personal");
    setIsEditModalOpen(true);
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      // 1. Update personal details
      await clientsAPI.updateClient(Number(id), {
        first_name: editFirstName,
        last_name: editLastName,
        nic_number: editNicNumber,
        date_of_birth: editDob,
        gender: editGender,
        phone_primary: editPhonePrimary,
        phone_secondary: editPhoneSecondary,
        email: editEmail,
        preferred_language: editLang,
      });

      // 2. Update address
      await api.post(`/clients/${id}/address`, {
        address_type: editAddressType,
        address_line_1: editAddressLine1,
        address_line_2: editAddressLine2,
        city: editCity,
        district: editDistrict,
        province: editProvince,
        is_primary: true,
      });

      // 3. Update business (only if name provided)
      if (editBusinessName) {
        await api.post(`/clients/${id}/business`, {
          business_name: editBusinessName,
          business_type: editBusinessType,
          years_in_operation: Number(editBusinessYears),
          number_of_employees: Number(editBusinessEmployees),
          monthly_revenue: Number(editBusinessRevenue),
        });
      }

      // 4. Update income
      await api.post(`/clients/${id}/income`, {
        income_source: editIncomeSource,
        monthly_income: Number(editMonthlyIncome),
        other_income: Number(editOtherIncome),
        monthly_expenses: Number(editMonthlyExpenses),
        existing_debt_monthly: Number(editExistingDebt),
        number_of_dependents: Number(editDependents),
      });

      toast.success("Profile updated successfully");
      setIsEditModalOpen(false);
      mutateClient();
    } catch (err: unknown) {
      toast.error("Failed to update profile details");
    } finally {
      setIsSaving(false);
    }
  };

  const resolvedParams = use(params);
  const id = resolvedParams.id;

  const { data: client, isLoading, mutate: mutateClient } = useSWR(`/clients/${id}/`, fetcher);
  const { data: loans } = useSWR(`/loans/applications/?client=${id}`, fetcher);

  const clientLoans = loans?.results || loans || [];
  const kycDocs = client?.documents || [];

  const loanColumns = [
    { id: "app", header: "App #", cell: (r: Record<string,unknown>) => <Link href={`/loans/${r.id}`}><span className="font-mono text-[13px] font-semibold text-blue-600 hover:underline">{String(r.application_number || "—")}</span></Link> },
    { id: "amount", header: "Amount", cell: (r: Record<string,unknown>) => <span className="text-[13px] font-medium">{formatCurrency(Number(r.requested_amount || 0))}</span> },
    { id: "purpose", header: "Purpose", cell: (r: Record<string,unknown>) => <span className="text-[13px]">{String(r.loan_purpose || "—").replace(/_/g, " ")}</span> },
    { id: "status", header: "Status", cell: (r: Record<string,unknown>) => <Badge status={String(r.status || "DRAFT")} /> },
    { id: "date", header: "Applied", cell: (r: Record<string,unknown>) => <span className="text-[12px] text-gray-400">{formatDate(String(r.created_at || new Date()))}</span> },
  ];

  const kycColumns = [
    { id: "type", header: "Document Type", cell: (r: Record<string,unknown>) => <span className="text-[13px]">{String(r.document_type || "—").replace(/_/g, " ")}</span> },
    { id: "status", header: "Status", cell: (r: Record<string,unknown>) => <Badge status={String(r.status || "PENDING")} /> },
    { id: "uploaded", header: "Uploaded", cell: (r: Record<string,unknown>) => <span className="text-[12px] text-gray-400">{formatDate(String(r.uploaded_at || new Date()))}</span> },
    { id: "actions", header: "Actions", cell: (r: Record<string,unknown>) => r.file ? <a href={String(r.file)} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline text-[13px]">View</a> : null },
  ];

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append("document_type", uploadType);
    formData.append("file", uploadFile);

    try {
      await api.post(`/kyc/${id}/documents/`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      toast.success("Document uploaded successfully");
      setIsUploadModalOpen(false);
      setUploadFile(null);
      mutateClient();
    } catch (error) {
      toast.error("Failed to upload document");
    } finally {
      setIsUploading(false);
    }
  };

  const handleVerifyClient = async () => {
    try {
      await api.post(`/clients/${id}/kyc/submit/`, {});
      toast.success("AI KYC Validation started");
      mutateClient();
    } catch (error) {
      toast.error("Failed to start AI KYC Validation");
    }
  };

  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [isCapturing, setIsCapturing] = useState(false);
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" } });
      setCameraStream(mediaStream);
      setTimeout(() => {
        const videoElement = document.getElementById("webcam-video") as HTMLVideoElement;
        if (videoElement) {
          videoElement.srcObject = mediaStream;
        }
      }, 300);
    } catch (err) {
      toast.error("Failed to access webcam camera. Check browser permissions.");
    }
  };

  useEffect(() => {
    if (isCameraOpen) {
      startCamera();
    } else {
      if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        setCameraStream(null);
      }
    }
    return () => {
      if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
      }
    };
  }, [isCameraOpen]);

  const handleCapture = async () => {
    const videoElement = document.getElementById("webcam-video") as HTMLVideoElement;
    if (!videoElement) return;
    setIsCapturing(true);
    try {
      const canvas = document.createElement("canvas");
      canvas.width = videoElement.videoWidth || 640;
      canvas.height = videoElement.videoHeight || 480;
      const ctx = canvas.getContext("2d");
      if (ctx) {
        ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
        canvas.toBlob(async (blob) => {
          if (blob) {
            const file = new File([blob], `selfie_${Date.now()}.jpg`, { type: "image/jpeg" });
            const formData = new FormData();
            formData.append("document_type", "PHOTO");
            formData.append("file", file);
            
            await api.post(`/kyc/${id}/documents/`, formData, {
              headers: { "Content-Type": "multipart/form-data" },
            });
            toast.success("Selfie captured and uploaded successfully!");
            setIsCameraOpen(false);
            mutateClient();
          }
        }, "image/jpeg", 0.9);
      }
    } catch (err) {
      toast.error("Failed to capture image");
    } finally {
      setIsCapturing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-6 w-48 animate-shimmer rounded" />
        <div className="h-40 animate-shimmer rounded-xl" />
      </div>
    );
  }

  if (!client) return (
    <div className="text-center py-16">
      <p className="text-[var(--text-muted)]">Client not found</p>
      <Link href="/clients"><Button variant="outline" className="mt-4">Back to Clients</Button></Link>
    </div>
  );

  const rawNotes = client?.data_quality_notes || "";
  let aiRecommend = "REQUIRES_REVIEW";
  let aiNotes = rawNotes;
  if (rawNotes.startsWith("[")) {
    const endIdx = rawNotes.indexOf("]");
    if (endIdx > -1) {
      aiRecommend = rawNotes.substring(1, endIdx);
      aiNotes = rawNotes.substring(endIdx + 1).trim();
    }
  }

  // Parse GATE TRIGGERED block out of notes for a cleaner UI
  let humanRationale = aiNotes;
  let technicalDetails = "";
  if (aiNotes.includes(" | ")) {
    const parts = aiNotes.split(" | ");
    technicalDetails = parts[0];
    humanRationale = parts.slice(1).join(" | ");
  } else if (aiNotes.startsWith("GATE TRIGGERED:")) {
    technicalDetails = aiNotes;
    humanRationale = "Human review required: System flags indicate unverified profile information or missing document files.";
  }

  // Ensure humanRationale does not display raw GATE TRIGGERED developer logs to staff
  if (humanRationale.includes("GATE TRIGGERED:")) {
    humanRationale = "Human review required: System flags indicate unverified profile information or missing document files.";
  }

  return (
    <div className="space-y-6">
      {/* Back */}
      <Link href="/clients">
        <Button variant="ghost" size="sm" icon={<ArrowLeft className="h-4 w-4" />}>All Clients</Button>
      </Link>

      {/* Warning banner for active status */}
      {client.status === "ACTIVE" && (
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-2xl text-amber-800 text-[13px] flex items-center gap-2">
          <Shield className="h-5 w-5 text-amber-600 flex-shrink-0" />
          <span>This client profile is <strong>Active</strong>. Details are locked for audit compliance and cannot be edited.</span>
        </div>
      )}

      {/* Client Header */}
      <div className="card p-6">
        <div className="flex flex-col md:flex-row gap-6 items-start">
          <div className="w-20 h-20 rounded-2xl gradient-primary flex items-center justify-center flex-shrink-0">
            <span className="text-white text-2xl font-bold">
              {getInitials(client.first_name, client.last_name)}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-3 mb-2">
              <h1 className="text-2xl font-bold text-[var(--text-primary)] truncate"> {/* FIX[BUG 15]: added truncate */}
                {client.first_name} {client.last_name}
              </h1>
              <Badge status={client.status} />
              <span className="font-mono text-[13px] text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full border border-blue-100">
                {client.client_number}
              </span>
            </div>
            <div className="flex flex-wrap gap-4 text-[13px] text-[var(--text-muted)]">
              <span>NIC: <span className="font-mono text-[var(--text-primary)]">{client.nic_number}</span></span>
              <span>📞 {client.phone_primary}</span>
              {client.email && <span>✉️ {client.email}</span>}
              <span>Registered: {formatDate(client.created_at)}</span>
            </div>
            {client.data_quality_score != null && (
              <div className="flex items-center gap-2 mt-3">
                <span className="text-[12px] text-[var(--text-muted)]">Data Quality Score:</span>
                <div className="progress-bar w-32"><div className={`progress-bar-fill ${client.data_quality_score >= 80 ? "bg-emerald-500" : client.data_quality_score >= 60 ? "bg-amber-500" : "bg-red-500"}`} style={{ width: `${client.data_quality_score}%` }} /></div>
                <span className="text-[13px] font-semibold">{client.data_quality_score}%</span>
              </div>
            )}
          </div>
          <div className="flex gap-2 flex-shrink-0">
            {can("clients:write") && (
              <Button 
                variant="outline" 
                size="sm" 
                onClick={openEditModal} 
                disabled={client.status === "ACTIVE"}
              >
                Edit Profile
              </Button>
            )}
            {can("loans:write") && <Link href={`/loans/new?client=${id}`}><Button size="sm" icon={<Plus className="h-4 w-4" />}>New Loan</Button></Link>}
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Active Loans" value={clientLoans.filter((l: Record<string,unknown>) => l.status === "DISBURSED").length} icon={<FileText className="h-5 w-5 text-blue-600" />} iconBg="bg-blue-50" />
        <StatCard title="Total Applications" value={clientLoans.length} icon={<Briefcase className="h-5 w-5 text-purple-600" />} iconBg="bg-purple-50" />
        <StatCard title="Total Borrowed" value={formatCurrency(clientLoans.reduce((sum: number, l: Record<string,unknown>) => sum + Number(l.requested_amount || 0), 0))} icon={<DollarSign className="h-5 w-5 text-emerald-600" />} iconBg="bg-emerald-50" />
        <StatCard title="KYC Documents" value={kycDocs.length} icon={<Shield className="h-5 w-5 text-amber-600" />} iconBg="bg-amber-50" />
      </div>

      {/* Tabs */}
      <div className="border-b border-[var(--border-color)]">
        <div className="flex gap-0">
          {TABS.map((t) => (
            <button key={t} onClick={() => setActiveTab(t)}
              className={`px-5 py-3 text-[14px] font-medium border-b-2 transition-colors ${activeTab === t ? "border-[var(--color-primary)] text-[var(--color-primary)]" : "border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)]"}`}>
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === "Overview" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-6"> {/* FIX[BUG 18]: added pt-6 */}
          <Card title="Personal Details">
            <dl className="space-y-3">
              {[
                ["Full Name", `${client.first_name} ${client.last_name}`],
                ["NIC Number", client.nic_number],
                ["Date of Birth", formatDate(client.date_of_birth)],
                ["Gender", client.gender === "M" ? "Male" : client.gender === "F" ? "Female" : "Other"],
                ["Primary Phone", client.phone_primary],
                ["Email", client.email || "—"],
                ["Language", client.preferred_language === "en" ? "English" : client.preferred_language === "si" ? "Sinhala" : "Tamil"],
              ].map(([label, value]) => (
                <div key={label} className="flex justify-between py-1 border-b border-gray-50 last:border-0">
                  <dt className="text-[13px] text-[var(--text-muted)]">{label}</dt>
                  <dd className="text-[13px] font-medium text-[var(--text-primary)]">{value}</dd>
                </div>
              ))}
            </dl>
          </Card>

          {client.business && (
            <Card title="Business Information">
              <dl className="space-y-3">
                {[
                  ["Business Name", client.business.business_name],
                  ["Type", client.business.business_type?.replace(/_/g, " ")],
                  ["Years Operating", `${client.business.years_in_operation} years`],
                  ["Employees", client.business.number_of_employees],
                  ["Monthly Revenue", formatCurrency(client.business.monthly_revenue || 0)],
                ].map(([label, value]) => (
                  <div key={label} className="flex justify-between py-1 border-b border-gray-50 last:border-0">
                    <dt className="text-[13px] text-[var(--text-muted)]">{label}</dt>
                    <dd className="text-[13px] font-medium text-[var(--text-primary)]">{String(value || "—")}</dd>
                  </div>
                ))}
              </dl>
            </Card>
          )}

          {client.income && (
            <Card title="Income & Expenses">
              <dl className="space-y-3">
                {[
                  ["Income Source", client.income.income_source?.replace(/_/g, " ")],
                  ["Monthly Income", formatCurrency(client.income.monthly_income || 0)],
                  ["Other Income", formatCurrency(client.income.other_income || 0)],
                  ["Monthly Expenses", formatCurrency(client.income.monthly_expenses || 0)],
                  ["Existing Debt", formatCurrency(client.income.existing_debt_monthly || 0)],
                  ["Dependents", client.income.number_of_dependents],
                ].map(([label, value]) => (
                  <div key={label} className="flex justify-between py-1 border-b border-gray-50 last:border-0">
                    <dt className="text-[13px] text-[var(--text-muted)]">{label}</dt>
                    <dd className="text-[13px] font-medium text-[var(--text-primary)]">{String(value || "—")}</dd>
                  </div>
                ))}
              </dl>
            </Card>
          )}
        </div>
      )}

      {activeTab === "KYC" && (
        <div className="pt-6 space-y-4"> {/* FIX[BUG 18]: added pt-6 wrapper */}
          {rawNotes && (
            <div className={`p-4 border rounded-2xl flex items-start gap-3 ${
              aiRecommend === "RECOMMEND_VERIFY" 
                ? "bg-emerald-50 border-emerald-200 text-emerald-800" 
                : aiRecommend === "HIGH_RISK_FLAG" 
                ? "bg-rose-50 border-rose-200 text-rose-800" 
                : "bg-amber-50 border-amber-200 text-amber-800"
            }`}>
              <Shield className={`h-5 w-5 mt-0.5 flex-shrink-0 ${
                aiRecommend === "RECOMMEND_VERIFY" 
                  ? "text-emerald-600" 
                  : aiRecommend === "HIGH_RISK_FLAG" 
                  ? "text-rose-600" 
                  : "text-amber-600"
              }`} />
              <div className="flex-1 min-w-0">
                <h4 className="font-bold text-[14px]">
                  {aiRecommend === "RECOMMEND_VERIFY" 
                    ? "AI Suggestion: READY TO VERIFY (Strong Recommendation)" 
                    : aiRecommend === "HIGH_RISK_FLAG" 
                    ? "AI Suggestion: HIGH RISK WARNING (Action Required)" 
                    : "AI Suggestion: REQUIRES MANUAL REVIEW"}
                </h4>
                <p className="text-[13px] mt-1 whitespace-pre-wrap">{humanRationale}</p>
              </div>
            </div>
          )}

          <Card 
            title="KYC Documents" 
            action={
              <div className="flex gap-2">
                {can("clients:write") && client?.status !== "VERIFIED" && (
                  <Button size="sm" variant="secondary" onClick={handleVerifyClient}>Run AI KYC Validation</Button>
                )}
                {can("clients:write") && (
                  <Button size="sm" variant="outline" icon={<Camera className="h-3.5 w-3.5" />} onClick={() => setIsCameraOpen(true)}>Take Client Photo</Button>
                )}
                {can("clients:write") && (
                  <Button size="sm" variant="outline" icon={<Plus className="h-3.5 w-3.5" />} onClick={() => setIsUploadModalOpen(true)}>Upload Document</Button>
                )}
              </div>
            }
          >
            <Table columns={kycColumns} data={kycDocs} emptyMessage="No KYC documents uploaded yet" />
          </Card>
        </div>
      )}

      {activeTab === "Loan History" && (
        <div className="pt-6"> {/* FIX[BUG 18]: added pt-6 wrapper */}
          <Card title="Loan Applications" action={can("loans:write") && <Link href={`/loans/new?client=${id}`}><Button size="sm" icon={<Plus className="h-3.5 w-3.5" />}>New Loan</Button></Link>}>
            <Table columns={loanColumns} data={clientLoans} emptyMessage="No loan applications found for this client" />
          </Card>
        </div>
      )}

      {activeTab === "Activity" && (
        <div className="pt-6"> {/* FIX[BUG 18]: added pt-6 wrapper */}
          <Card title="Client Activity Timeline">
            <div className="space-y-4">
              {clientLoans.slice(0, 5).map((l: Record<string,unknown>, i: number) => (
                <div key={String(l.id)} className="flex gap-4">
                  <div className="flex flex-col items-center">
                    <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                      <FileText className="h-4 w-4 text-blue-600" />
                    </div>
                    {i < clientLoans.length - 1 && <div className="w-0.5 h-6 bg-gray-200 mt-2" />}
                  </div>
                  <div className="pb-4 min-w-0"> {/* FIX[BUG 15]: min-w-0 */}
                    <p className="text-[13px] font-medium text-[var(--text-primary)] truncate">Loan application {String(l.application_number)} — <Badge status={String(l.status || "DRAFT")} /></p>
                    <p className="text-[12px] text-gray-400 mt-0.5">{formatDate(String(l.created_at || new Date()))}</p>
                  </div>
                </div>
              ))}
              {clientLoans.length === 0 && <p className="text-[var(--text-muted)] text-[14px]">No activity recorded yet</p>}
            </div>
          </Card>
        </div>
      )}

      <Modal isOpen={isCameraOpen} onClose={() => {
        if (!isCapturing) {
          setIsCameraOpen(false);
        }
      }} title="Capture Client Photo">
        <div className="space-y-4">
          <div className="relative bg-black rounded-2xl overflow-hidden aspect-video flex items-center justify-center border border-gray-100">
            <video id="webcam-video" autoPlay playsInline className="w-full h-full object-cover transform -scale-x-100" />
            {isCapturing && (
              <div className="absolute inset-0 bg-black/50 flex items-center justify-center text-white text-sm font-semibold">
                Capturing...
              </div>
            )}
          </div>
          <div className="flex gap-3">
            <Button type="button" variant="outline" className="flex-1" onClick={() => setIsCameraOpen(false)} disabled={isCapturing}>
              Cancel
            </Button>
            <Button type="button" variant="primary" className="flex-1" onClick={handleCapture} loading={isCapturing}>
              Snap Photo
            </Button>
          </div>
        </div>
      </Modal>

      <Modal isOpen={isUploadModalOpen} onClose={() => !isUploading && setIsUploadModalOpen(false)} title="Upload KYC Document">
        <form onSubmit={handleUpload} className="space-y-4">
          <div>
            <label className="form-label">Document Type</label>
            <select
              value={uploadType}
              onChange={(e) => setUploadType(e.target.value)}
              className="form-input px-3"
              disabled={isUploading}
            >
              <option value="NIC">NIC</option>
              <option value="PASSPORT">Passport</option>
              <option value="DRIVING_LICENSE">Driving License</option>
              <option value="UTILITY_BILL">Utility Bill</option>
              <option value="BANK_STATEMENT">Bank Statement</option>
              <option value="OTHER">Other</option>
            </select>
          </div>
          <div>
            <label className="form-label flex justify-between">
              File
              <span className="text-[11px] text-gray-400 font-normal">Max 5MB (PDF, JPG, PNG)</span>
            </label>
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

      {/* Edit Profile Modal */}
      <Modal isOpen={isEditModalOpen} onClose={() => !isSaving && setIsEditModalOpen(false)} title="Edit Client Profile">
        <form onSubmit={handleEditSubmit} className="space-y-4">
          {/* Tab Selection */}
          <div className="flex border-b border-gray-100 mb-4 overflow-x-auto scrollbar-none gap-2">
            {[
              { id: "personal", label: "1. Personal Info" },
              { id: "address", label: "2. Address" },
              { id: "business", label: "3. Business" },
              { id: "income", label: "4. Income" },
            ].map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setModalTab(tab.id)}
                className={`px-4 py-2 text-xs font-semibold whitespace-nowrap border-b-2 transition-colors duration-200 ${modalTab === tab.id ? "border-blue-600 text-blue-600 font-bold" : "border-transparent text-gray-500 hover:text-gray-700"}`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Personal Info Tab */}
          {modalTab === "personal" && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Input label="First Name *" value={editFirstName} onChange={(e) => setEditFirstName(e.target.value)} required disabled={isSaving} />
                <Input label="Last Name *" value={editLastName} onChange={(e) => setEditLastName(e.target.value)} required disabled={isSaving} />
              </div>
              <Input label="NIC Number *" value={editNicNumber} onChange={(e) => setEditNicNumber(e.target.value)} required disabled={isSaving} />
              <div className="grid grid-cols-2 gap-4">
                <Input label="Date of Birth *" type="date" value={editDob} onChange={(e) => setEditDob(e.target.value)} required disabled={isSaving} />
                <Select 
                  label="Gender *" 
                  value={editGender} 
                  onChange={(e) => setEditGender(e.target.value)} 
                  options={[
                    { value: "M", label: "Male" },
                    { value: "F", label: "Female" },
                    { value: "O", label: "Other" }
                  ]} 
                  disabled={isSaving} 
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Input label="Primary Phone *" value={editPhonePrimary} onChange={(e) => setEditPhonePrimary(e.target.value)} required disabled={isSaving} />
                <Input label="Secondary Phone" value={editPhoneSecondary} onChange={(e) => setEditPhoneSecondary(e.target.value)} disabled={isSaving} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Input label="Email Address" type="email" value={editEmail} onChange={(e) => setEditEmail(e.target.value)} disabled={isSaving} />
                <Select 
                  label="Preferred Language" 
                  value={editLang} 
                  onChange={(e) => setEditLang(e.target.value)} 
                  options={[
                    { value: "en", label: "English" },
                    { value: "si", label: "Sinhala" },
                    { value: "ta", label: "Tamil" }
                  ]} 
                  disabled={isSaving} 
                />
              </div>
            </div>
          )}

          {/* Address Tab */}
          {modalTab === "address" && (
            <div className="space-y-4">
              <Select 
                label="Address Type" 
                value={editAddressType} 
                onChange={(e) => setEditAddressType(e.target.value)} 
                options={[
                  { value: "HOME", label: "Home" },
                  { value: "BUSINESS", label: "Business" },
                  { value: "POSTAL", label: "Postal" }
                ]} 
                disabled={isSaving} 
              />
              <Input label="Address Line 1 *" value={editAddressLine1} onChange={(e) => setEditAddressLine1(e.target.value)} required disabled={isSaving} />
              <Input label="Address Line 2" value={editAddressLine2} onChange={(e) => setEditAddressLine2(e.target.value)} disabled={isSaving} />
              <div className="grid grid-cols-3 gap-4">
                <Input label="City *" value={editCity} onChange={(e) => setEditCity(e.target.value)} required disabled={isSaving} />
                <Input label="District *" value={editDistrict} onChange={(e) => setEditDistrict(e.target.value)} required disabled={isSaving} />
                <Input label="Province *" value={editProvince} onChange={(e) => setEditProvince(e.target.value)} required disabled={isSaving} />
              </div>
            </div>
          )}

          {/* Business Tab */}
          {modalTab === "business" && (
            <div className="space-y-4">
              <Input label="Business Name" placeholder="Leave empty if not applicable" value={editBusinessName} onChange={(e) => setEditBusinessName(e.target.value)} disabled={isSaving} />
              {editBusinessName && (
                <>
                  <Select 
                    label="Business Type" 
                    value={editBusinessType} 
                    onChange={(e) => setEditBusinessType(e.target.value)} 
                    options={[
                      { value: "SOLE_PROPRIETOR", label: "Sole Proprietor" },
                      { value: "PARTNERSHIP", label: "Partnership" },
                      { value: "PRIVATE_LIMITED", label: "Private Limited" },
                      { value: "INFORMAL", label: "Informal Business" },
                      { value: "FARMING", label: "Farming" },
                      { value: "OTHER", label: "Other" }
                    ]} 
                    disabled={isSaving} 
                  />
                  <div className="grid grid-cols-2 gap-4">
                    <Input label="Years in Operation" type="number" min={0} value={editBusinessYears} onChange={(e) => setEditBusinessYears(Number(e.target.value))} disabled={isSaving} />
                    <Input label="Number of Employees" type="number" min={0} value={editBusinessEmployees} onChange={(e) => setEditBusinessEmployees(Number(e.target.value))} disabled={isSaving} />
                  </div>
                  <Input label="Monthly Revenue (LKR)" type="number" min={0} value={editBusinessRevenue} onChange={(e) => setEditBusinessRevenue(Number(e.target.value))} disabled={isSaving} />
                </>
              )}
            </div>
          )}

          {/* Income Tab */}
          {modalTab === "income" && (
            <div className="space-y-4">
              <Select 
                label="Income Source" 
                value={editIncomeSource} 
                onChange={(e) => setEditIncomeSource(e.target.value)} 
                options={[
                  { value: "BUSINESS", label: "Business Income" },
                  { value: "SALARY", label: "Salary" },
                  { value: "AGRICULTURE", label: "Agriculture" },
                  { value: "REMITTANCE", label: "Remittance" },
                  { value: "PENSION", label: "Pension" },
                  { value: "OTHER", label: "Other" }
                ]} 
                disabled={isSaving} 
              />
              <div className="grid grid-cols-2 gap-4">
                <Input label="Monthly Income (LKR) *" type="number" min={0} value={editMonthlyIncome} onChange={(e) => setEditMonthlyIncome(Number(e.target.value))} required disabled={isSaving} />
                <Input label="Other Income (LKR)" type="number" min={0} value={editOtherIncome} onChange={(e) => setEditOtherIncome(Number(e.target.value))} disabled={isSaving} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Input label="Monthly Expenses (LKR)" type="number" min={0} value={editMonthlyExpenses} onChange={(e) => setEditMonthlyExpenses(Number(e.target.value))} disabled={isSaving} />
                <Input label="Existing Debt Payments (LKR)" type="number" min={0} value={editExistingDebt} onChange={(e) => setEditExistingDebt(Number(e.target.value))} disabled={isSaving} />
              </div>
              <Input label="Number of Dependents" type="number" min={0} max={20} value={editDependents} onChange={(e) => setEditDependents(Number(e.target.value))} disabled={isSaving} />
            </div>
          )}

          <div className="pt-4 flex gap-3 border-t border-gray-100">
            <Button type="button" variant="outline" className="flex-1" onClick={() => setIsEditModalOpen(false)} disabled={isSaving}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" className="flex-1" loading={isSaving}>
              Save Changes
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
