import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { format, formatDistanceToNow } from "date-fns";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(
  amount: number | string,
  currency = "LKR"
): string {
  const num = typeof amount === "string" ? parseFloat(amount) : amount;
  if (isNaN(num)) return `${currency} 0.00`;
  return `${currency} ${num.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

export function normalizeArrayData<T>(value: unknown): T[] {
  if (Array.isArray(value)) {
    return value as T[];
  }

  if (value && typeof value === "object") {
    const maybeResults = (value as { results?: unknown }).results;
    if (Array.isArray(maybeResults)) {
      return maybeResults as T[];
    }
  }

  return [];
}

export function formatDate(date: string | Date): string {
  if (!date) return "-";
  return format(new Date(date), "dd MMM yyyy");
}

export function formatDateTime(date: string | Date): string {
  if (!date) return "-";
  return format(new Date(date), "dd MMM yyyy, hh:mm a");
}

export function formatRelativeTime(date: string | Date): string {
  if (!date) return "-";
  return formatDistanceToNow(new Date(date), { addSuffix: true });
}

export function getStatusColor(status: string): string {
  const s = status?.toUpperCase();
  const map: Record<string, string> = {
    ACTIVE: "text-emerald-700",
    APPROVED: "text-emerald-700",
    VERIFIED: "text-emerald-700",
    DISBURSED: "text-emerald-700",
    CLOSED: "text-emerald-700",
    COMPLETED: "text-emerald-700", // FIX[BUG 14]: added COMPLETED
    PAID: "text-emerald-700",
    LOW: "text-emerald-700",
    PENDING: "text-amber-700",
    SUBMITTED: "text-amber-700",
    KYC_SUBMITTED: "text-amber-700",
    INFO: "text-blue-700",
    AI_SCREENING: "text-blue-700",
    RISK_REVIEWED: "text-blue-700",
    MANAGER_REVIEW: "text-blue-700",
    COMMITTEE_REVIEW: "text-purple-700",
    MEDIUM: "text-amber-700",
    MORE_INFO_REQUIRED: "text-amber-700",
    PARTIAL: "text-amber-700",
    OVERDUE: "text-red-700",
    REJECTED: "text-red-700",
    SUSPENDED: "text-red-700",
    DEFAULTED: "text-red-700",
    WRITTEN_OFF: "text-red-700",
    HIGH: "text-red-700",
    CRITICAL: "text-red-700",
    HARD: "text-red-700",
    SOFT: "text-blue-700",
    CANCELLED: "text-gray-700",
    DRAFT: "text-gray-700",
    RESCHEDULED: "text-indigo-700",
    PAUSED: "text-red-700",
    AI_HYBRID: "text-blue-700",
    RULES_ONLY: "text-indigo-700",
    ONLINE: "text-emerald-700",
    DEGRADED: "text-amber-700",
    OFFLINE: "text-red-700",
    MANUAL_MODE_ACTIVE: "text-purple-700",
    OPEN: "text-amber-700",
    RESOLVED: "text-emerald-700",
  };
  return map[s] || "text-gray-700";
}

export function getStatusBgColor(status: string): string {
  const s = status?.toUpperCase();
  const map: Record<string, string> = {
    ACTIVE: "bg-emerald-50 border-emerald-200",
    APPROVED: "bg-emerald-50 border-emerald-200",
    VERIFIED: "bg-emerald-50 border-emerald-200",
    DISBURSED: "bg-emerald-50 border-emerald-200",
    CLOSED: "bg-emerald-50 border-emerald-200",
    COMPLETED: "bg-emerald-50 border-emerald-200", // FIX[BUG 14]: added COMPLETED
    PAID: "bg-emerald-50 border-emerald-200",
    LOW: "bg-emerald-50 border-emerald-200",
    PENDING: "bg-amber-50 border-amber-200",
    SUBMITTED: "bg-amber-50 border-amber-200",
    KYC_SUBMITTED: "bg-amber-50 border-amber-200",
    INFO: "bg-blue-50 border-blue-200",
    AI_SCREENING: "bg-blue-50 border-blue-200",
    RISK_REVIEWED: "bg-blue-50 border-blue-200",
    MANAGER_REVIEW: "bg-blue-50 border-blue-200",
    COMMITTEE_REVIEW: "bg-purple-50 border-purple-200",
    MEDIUM: "bg-amber-50 border-amber-200",
    MORE_INFO_REQUIRED: "bg-amber-50 border-amber-200",
    PARTIAL: "bg-amber-50 border-amber-200",
    OVERDUE: "bg-red-50 border-red-200",
    REJECTED: "bg-red-50 border-red-200",
    SUSPENDED: "bg-red-50 border-red-200",
    DEFAULTED: "bg-red-50 border-red-200",
    WRITTEN_OFF: "bg-red-50 border-red-200",
    HIGH: "bg-red-50 border-red-200",
    CRITICAL: "bg-red-50 border-red-200",
    HARD: "bg-red-50 border-red-200",
    SOFT: "bg-blue-50 border-blue-200",
    CANCELLED: "bg-gray-50 border-gray-200",
    DRAFT: "bg-gray-50 border-gray-200",
    RESCHEDULED: "bg-indigo-50 border-indigo-200",
    PAUSED: "bg-red-50 border-red-200",
    AI_HYBRID: "bg-blue-50 border-blue-200",
    RULES_ONLY: "bg-indigo-50 border-indigo-200",
    ONLINE: "bg-emerald-50 border-emerald-200",
    DEGRADED: "bg-amber-50 border-amber-200",
    OFFLINE: "bg-red-50 border-red-200",
    MANUAL_MODE_ACTIVE: "bg-purple-50 border-purple-200",
    OPEN: "bg-amber-50 border-amber-200",
    RESOLVED: "bg-emerald-50 border-emerald-200",
  };
  return map[s] || "bg-gray-50 border-gray-200";
}

export function truncate(str: string, maxLength: number): string {
  if (!str) return "";
  return str.length > maxLength ? str.slice(0, maxLength) + "..." : str;
}

export function capitalizeFirst(str: string): string {
  if (!str) return "";
  return str.charAt(0).toUpperCase() + str.slice(1).replace(/_/g, " ");
}

export function getInitials(
  firstName?: string,
  lastName?: string,
  username?: string
): string {
  const f = firstName?.trim()?.charAt(0)?.toUpperCase() || "";
  const l = lastName?.trim()?.charAt(0)?.toUpperCase() || "";
  if (f + l) return f + l;

  if (username && username.trim().length > 0) {
    const cleanU = username.trim();
    if (cleanU.length >= 2) {
      return cleanU.substring(0, 2).toUpperCase();
    }
    return cleanU.charAt(0).toUpperCase();
  }

  return "??";
}

export function calculateEMI(
  principal: number,
  annualRate: number,
  months: number
): number {
  if (principal <= 0 || months <= 0) return 0;
  if (annualRate <= 0) return principal / months;
  const r = annualRate / 12 / 100;
  const emi = (principal * r * Math.pow(1 + r, months)) / (Math.pow(1 + r, months) - 1);
  return Math.round(emi * 100) / 100;
}
