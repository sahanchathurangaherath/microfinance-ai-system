"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn, getInitials } from "@/lib/utils";
import { usePermissions } from "@/lib/permissions";
import { useAuthStore } from "@/lib/store";
import {
  LayoutDashboard, Users, FileText, CheckCircle, CreditCard,
  TrendingDown, AlertTriangle, BarChart2, Shield, UserCog,
  Bell, User, ChevronLeft, ChevronRight, X, Building2, Brain,
  MessageSquare,
} from "lucide-react";

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
  permission?: string;
  badge?: number;
}

interface NavGroup {
  title: string;
  items: NavItem[];
}

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  isMobileOpen: boolean;
  onMobileClose: () => void;
  unreadNotifications?: number;
}

export default function Sidebar({
  collapsed,
  onToggle,
  isMobileOpen,
  onMobileClose,
  unreadNotifications = 0,
}: SidebarProps) {
  const pathname = usePathname();
  const { can, role } = usePermissions();
  const user = useAuthStore((s) => s.user);

  const navGroups: NavGroup[] = [
    {
      title: "Overview",
      items: [
        {
          label: "Dashboard",
          href: `/dashboard/${role === "admin" ? "admin" : role === "loan_officer" ? "loan-officer" : role === "risk_analyst" ? "risk-analyst" : role === "branch_manager" ? "branch-manager" : role === "credit_committee" ? "credit-committee" : role === "collections_officer" ? "collections" : role === "compliance_officer" ? "compliance" : "finance"}`,
          icon: <LayoutDashboard className="h-5 w-5" />,
        },
      ],
    },
    {
      title: "Clients",
      items: [
        {
          label: "Clients",
          href: "/clients",
          icon: <Users className="h-5 w-5" />,
          permission: "clients:read",
        },
      ],
    },
    {
      title: "Lending",
      items: [
        {
          label: "Loan Applications",
          href: "/loans",
          icon: <FileText className="h-5 w-5" />,
          permission: "loans:read",
        },
        {
          label: "Approvals",
          href: "/approvals",
          icon: <CheckCircle className="h-5 w-5" />,
          permission: "approvals:read",
        },
        {
          label: "Repayments",
          href: "/repayments",
          icon: <CreditCard className="h-5 w-5" />,
          permission: "repayments:read",
        },
      ],
    },
    {
      title: "Operations",
      items: [
        {
          label: "Collections",
          href: "/collections",
          icon: <TrendingDown className="h-5 w-5" />,
          permission: "collections:read",
        },
        {
          label: "Fraud Alerts",
          href: "/fraud",
          icon: <AlertTriangle className="h-5 w-5" />,
          permission: "fraud:read",
        },
        {
          label: "Reports",
          href: "/reports",
          icon: <BarChart2 className="h-5 w-5" />,
          permission: "reports:read",
        },
        {
          label: "Communication Queue",
          href: "/notifications-queue",
          icon: <MessageSquare className="h-5 w-5" />,
          permission: "communication_queue:read",
        },
      ],
    },
    {
      title: "Admin",
      items: [
        {
          label: "Audit Trail",
          href: "/audit",
          icon: <Shield className="h-5 w-5" />,
          permission: "audit:read",
        },
        {
          label: "AI Control Panel",
          href: "/admin/ai-control-panel",
          icon: <Brain className="h-5 w-5" />,
          permission: "ai_control:read",
        },
        {
          label: "User Management",
          href: "/users",
          icon: <UserCog className="h-5 w-5" />,
          permission: "users:read",
        },
        {
          label: "Notifications",
          href: "/notifications",
          icon: <Bell className="h-5 w-5" />,
          permission: "notifications:read",
          badge: unreadNotifications,
        },
      ],
    },
    {
      title: "Account",
      items: [
        {
          label: "My Profile",
          href: "/profile",
          icon: <User className="h-5 w-5" />,
          permission: "profile:read",
        },
      ],
    },
  ];

  // Filter items based on role permissions
  const finalGroups = navGroups.map((group) => ({
    ...group,
    items: group.items.filter((item) =>
      !item.permission || can(item.permission)
    ),
  })).filter((group) => group.items.length > 0);

  const isActive = (href: string) =>
    pathname === href || pathname.startsWith(href + "/");

  const sidebarContent = (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className={cn(
        "flex items-center gap-3 px-4 py-5 sm:px-5 border-b border-[var(--border-color)]",
        collapsed ? "justify-center" : ""
      )}>
        <div className="w-9 h-9 rounded-xl gradient-primary flex items-center justify-center flex-shrink-0">
          <Building2 className="h-5 w-5 text-white" />
        </div>
        {!collapsed && (
          <div>
            <p className="text-[14px] font-bold text-[var(--text-primary)] leading-tight">
              MicroFinance AI
            </p>
            <p className="text-[11px] text-[var(--text-muted)]">Management System</p>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-4 px-3">
        {finalGroups.map((group) => (
          <div key={group.title} className="mb-4">
            {!collapsed && (
              <p className="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-widest px-3 mb-2">
                {group.title}
              </p>
            )}
            {group.items.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={onMobileClose}
                className={cn(
                  "relative flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
                  isActive(item.href)
                    ? "bg-blue-50 text-blue-700 font-semibold"
                    : "text-gray-600 hover:bg-gray-50",
                  collapsed && "justify-center px-2 gap-0" // FIX[BUG 12]: collapsed gap-0 and px-2
                )}
                title={collapsed ? item.label : undefined}
              >
                <span className={cn(
                  "flex h-5 w-5 items-center justify-center rounded-lg text-gray-500 transition-colors flex-shrink-0",
                  isActive(item.href) && "text-blue-600"
                )}>
                  {item.icon}
                </span>
                {!collapsed && (
                  <span className="flex-1 text-[13px]">{item.label}</span>
                )}
                {item.badge !== undefined && item.badge > 0 && (
                  <span className={cn(
                    "bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center",
                    collapsed ? "absolute -top-1 -right-1 w-4 h-4" : "w-5 h-5"
                  )}>
                    {item.badge > 99 ? "99+" : item.badge}
                  </span>
                )}
              </Link>
            ))}
          </div>
        ))}
      </nav>

      {/* Footer / User Profile & Collapse Toggle */}
      <div className={cn(
        "border-t border-[var(--border-color)] p-3 flex items-center transition-all",
        collapsed ? "flex-col justify-center gap-3" : "justify-between"
      )}>
        {user && !collapsed && (
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="h-8 w-8 rounded-full flex items-center justify-center text-sm font-medium bg-blue-100 text-blue-700 flex-shrink-0">
              {getInitials(user.first_name, user.last_name, user.username)}
            </div>
            <div className="min-w-0">
              <p className="text-[13px] font-semibold text-[var(--text-primary)] truncate leading-tight">
                {user.first_name || user.username} {user.last_name || ""}
              </p>
              <p className="text-[11px] text-[var(--text-muted)] truncate">
                {user.role_display}
              </p>
            </div>
          </div>
        )}
        {user && collapsed && (
          <div className="h-8 w-8 rounded-full flex items-center justify-center text-sm font-medium bg-blue-100 text-blue-700 flex-shrink-0" title={user.username}>
            {getInitials(user.first_name, user.last_name, user.username)}
          </div>
        )}
        <button
          onClick={onToggle}
          className={cn(
            "hidden lg:flex items-center justify-center h-8 w-8 rounded-full hover:bg-gray-100 transition-colors flex-shrink-0",
            collapsed ? "" : "ml-1"
          )}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4 text-[var(--text-secondary)]" />
          ) : (
            <ChevronLeft className="h-4 w-4 text-[var(--text-secondary)]" />
          )}
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <aside
        className={cn(
          "hidden lg:flex flex-col flex-shrink-0 h-full overflow-y-auto border-r border-gray-200 bg-white transition-all duration-300",
          collapsed ? "w-16" : "w-52"
        )}
      >
        {sidebarContent}
      </aside>

      {/* Mobile Sidebar */}
      {isMobileOpen && (
        <>
          <div
            className="lg:hidden fixed inset-0 bg-black/40 z-40"
            onClick={onMobileClose}
          />
          <aside className={cn(
            "lg:hidden fixed top-0 left-0 h-full w-52 bg-[var(--bg-sidebar)] border-r border-[var(--border-color)] shadow-xl z-50 transition-transform duration-300",
            isMobileOpen ? "translate-x-0" : "-translate-x-full"
          )}>
            <button
              onClick={onMobileClose}
              className="absolute top-4 right-4 p-1.5 rounded-lg hover:bg-gray-100"
            >
              <X className="h-5 w-5 text-[var(--text-secondary)]" />
            </button>
            {sidebarContent}
          </aside>
        </>
      )}
    </>
  );
}
