/* eslint-disable react-hooks/set-state-in-effect */
"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuthStore } from "@/lib/store";
import { authAPI } from "@/lib/api";
import { clearTokens, getRefreshToken } from "@/lib/auth";
import { cn } from "@/lib/utils";
import Sidebar from "@/components/layout/Sidebar";
import Topbar from "@/components/layout/Topbar";
import ToastContainer from "@/components/ui/Toast";
import Modal from "@/components/ui/Modal";
import Button from "@/components/ui/Button";
import Spinner from "@/components/ui/Spinner";

const IDLE_TIMEOUT = 29 * 60 * 1000; // 29 minutes

function getPageTitle(pathname: string): string {
  // Normalize trailing slashes
  const cleanPathname = pathname !== "/" && pathname.endsWith("/") ? pathname.slice(0, -1) : pathname;

  const map: Record<string, string> = {
    "/dashboard/admin": "Admin Dashboard",
    "/dashboard/loan-officer": "Loan Officer Dashboard",
    "/dashboard/risk-analyst": "Risk Analyst Dashboard",
    "/dashboard/branch-manager": "Branch Manager Dashboard",
    "/dashboard/credit-committee": "Credit Committee Dashboard",
    "/dashboard/collections": "Collections Dashboard",
    "/dashboard/compliance": "Compliance Dashboard",
    "/dashboard/finance": "Finance Dashboard",
    "/clients": "Clients",
    "/clients/new": "Register New Client",
    "/loans": "Loan Applications",
    "/loans/new": "New Loan Application",
    "/approvals": "Approval Queue",
    "/repayments": "Repayments",
    "/collections": "Collections",
    "/fraud": "Fraud Alerts",
    "/reports": "Reports & Analytics",
    "/audit": "Audit Trail",
    "/notifications": "Notifications",
    "/users": "User Management",
    "/profile": "My Profile",
  };

  // Exact match
  if (map[cleanPathname]) return map[cleanPathname];

  // Prefix match for dynamic routes
  if (cleanPathname.startsWith("/clients/") && cleanPathname !== "/clients/new" && cleanPathname !== "/clients/") return "Client Profile";
  if (cleanPathname.startsWith("/loans/") && cleanPathname !== "/loans/new" && cleanPathname !== "/loans/") return "Loan Application";
  if (cleanPathname.startsWith("/approvals/")) return "Approval Detail";

  return "MicroFinance AI";
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, setAuth, setLoading, isLoading } = useAuthStore();

  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [sessionWarning, setSessionWarning] = useState(false);
  const [isMounted, setIsMounted] = useState(false);

  const idleTimer = useRef<NodeJS.Timeout | null>(null);

  const pageTitle = getPageTitle(pathname);

  // Restore auth from API if store is empty but cookie exists
  useEffect(() => {
    setIsMounted(true);
    if (!isAuthenticated) {
      setLoading(true);
      authAPI.getCurrentUser()
        .then((res) => {
          setAuth(res.data);
        })
        .catch(() => {
          clearTokens();
          router.replace("/login");
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []); // eslint-disable-line

  // Close mobile sidebar on resize to desktop screen
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024) {
        setMobileOpen(false);
      }
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Session timeout idle detection
  const resetIdleTimer = useCallback(() => {
    if (idleTimer.current) clearTimeout(idleTimer.current);
    setSessionWarning(false);
    idleTimer.current = setTimeout(() => {
      setSessionWarning(true);
    }, IDLE_TIMEOUT);
  }, []);

  useEffect(() => {
    const events = ["mousedown", "keydown", "scroll", "touchstart"];
    events.forEach((e) => window.addEventListener(e, resetIdleTimer));
    resetIdleTimer();
    return () => {
      events.forEach((e) => window.removeEventListener(e, resetIdleTimer));
      if (idleTimer.current) clearTimeout(idleTimer.current);
    };
  }, [resetIdleTimer]);

  const handleStaySignedIn = () => {
    setSessionWarning(false);
    resetIdleTimer();
  };

  const handleSessionLogout = async () => {
    try {
      const refresh = getRefreshToken();
      if (refresh) await authAPI.logout(refresh);
    } catch {}
    clearTokens();
    useAuthStore.getState().logout();
    router.replace("/login");
  };

  if (!isMounted || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--bg-primary)] px-4 sm:px-6">
        <div className="flex flex-col items-center gap-3 rounded-[24px] border border-[var(--border-color)] bg-white/90 px-6 py-8 shadow-[0_24px_60px_-28px_rgba(15,23,42,0.22)] backdrop-blur sm:px-8">
          <Spinner size="lg" />
          <p className="text-[var(--text-muted)] text-sm">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--bg-primary)] text-[var(--text-primary)]">
      {/* Sidebar */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((v) => !v)}
        isMobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
      />

      {/* Main column */}
      <div className="flex flex-col flex-1 min-w-0 h-full overflow-hidden">
        <Topbar
          onMenuToggle={() => setMobileOpen((v) => !v)}
          pageTitle={pageTitle}
          sidebarCollapsed={sidebarCollapsed}
        />

        {/* Main content */}
        <main className="flex-1 overflow-y-auto min-h-0 flex flex-col"> {/* FIX: added flex flex-col */}
          <div className="page-shell flex-1 flex flex-col"> {/* FIX: added flex-1 flex flex-col */}
            {children}
          </div>
        </main>
      </div>

      {/* Toast notifications */}
      <ToastContainer />

      {/* Session Timeout Warning */}
      <Modal
        isOpen={sessionWarning}
        onClose={handleStaySignedIn}
        title="Session Expiring Soon"
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-[14px] text-[var(--text-secondary)]">
            You will be automatically signed out in{" "}
            <span className="font-semibold text-amber-600">1 minute</span> due
            to inactivity. Would you like to stay signed in?
          </p>
          <div className="flex gap-3">
            <Button variant="primary" onClick={handleStaySignedIn} className="flex-1">
              Stay Signed In
            </Button>
            <Button variant="danger" onClick={handleSessionLogout} className="flex-1">
              Sign Out Now
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
