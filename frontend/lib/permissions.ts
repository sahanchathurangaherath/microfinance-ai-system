"use client";

import { useAuthStore } from "./store";

// ─── Permission definitions per role ─────────────────────
export const ROLE_PERMISSIONS: Record<string, string[]> = {
  admin: ["*"],
  loan_officer: [
    "clients:read", "clients:write",
    "loans:read", "loans:write",
    "repayments:read",
    "notifications:read",
    "profile:read",
    "reports:read",
  ],
  risk_analyst: [
    "clients:read",
    "loans:read",
    "risk:read", "risk:write",
    "approvals:read", "approvals:write",
    "reports:read",
    "notifications:read",
    "profile:read",
  ],
  branch_manager: [
    "clients:read", "clients:write",
    "loans:read",
    "approvals:read", "approvals:write",
    "repayments:read",
    "collections:read",
    "reports:read",
    "notifications:read",
    "profile:read",
  ],
  credit_committee: [
    "clients:read",
    "loans:read",
    "approvals:read", "approvals:write",
    "notifications:read",
    "profile:read",
  ],
  collections_officer: [
    "clients:read",
    "loans:read",
    "repayments:read",
    "collections:read", "collections:write",
    "reports:read",
    "notifications:read",
    "profile:read",
  ],
  compliance_officer: [
    "clients:read",
    "loans:read",
    "fraud:read",
    "audit:read",
    "reports:read",
    "collections:read",
    "repayments:read",
    "notifications:read",
    "profile:read",
  ],
  finance_staff: [
    "clients:read",
    "loans:read",
    "repayments:read", "repayments:write",
    "reports:read",
    "notifications:read",
    "profile:read",
  ],
};

// ─── Role → dashboard home page ──────────────────────────
export const ROLE_HOME_PAGES: Record<string, string> = {
  admin: "/dashboard/admin",
  loan_officer: "/dashboard/loan-officer",
  risk_analyst: "/dashboard/risk-analyst",
  branch_manager: "/dashboard/branch-manager",
  credit_committee: "/dashboard/credit-committee",
  collections_officer: "/dashboard/collections",
  compliance_officer: "/dashboard/compliance",
  finance_staff: "/dashboard/finance",
};

export const ROLE_LABELS: Record<string, string> = {
  admin: "System Administrator",
  loan_officer: "Loan Officer",
  risk_analyst: "Risk Analyst",
  branch_manager: "Branch Manager",
  credit_committee: "Credit Committee",
  collections_officer: "Collections Officer",
  compliance_officer: "Compliance Officer",
  finance_staff: "Finance Staff",
};

// ─── Access check utility ────────────────────────────────
export function canAccess(role: string, permission: string): boolean {
  const perms = ROLE_PERMISSIONS[role];
  if (!perms) return false;
  if (perms.includes("*")) return true;
  return perms.includes(permission);
}

// ─── React hook ──────────────────────────────────────────
export function usePermissions() {
  const user = useAuthStore((s) => s.user);
  const role = user?.role || "";

  return {
    role,
    can: (permission: string) => canAccess(role, permission),
    isAdmin: role === "admin",
    isLoanOfficer: role === "loan_officer",
    isRiskAnalyst: role === "risk_analyst",
    isBranchManager: role === "branch_manager",
    isCreditCommittee: role === "credit_committee",
    isCollectionsOfficer: role === "collections_officer",
    isComplianceOfficer: role === "compliance_officer",
    isFinanceStaff: role === "finance_staff",
  };
}
