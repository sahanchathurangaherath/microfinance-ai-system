"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Menu, Search, Bell, ChevronDown, User, LogOut, Settings } from "lucide-react";
import { useAuthStore } from "@/lib/store";
import { clearTokens, getRefreshToken } from "@/lib/auth";
import { authAPI, fetcher } from "@/lib/api";
import { getInitials, cn } from "@/lib/utils";
import useSWR from "swr";

interface TopbarProps {
  onMenuToggle: () => void;
  pageTitle: string;
  sidebarCollapsed?: boolean;
}

export default function Topbar({
  onMenuToggle,
  pageTitle,
  sidebarCollapsed = false,
}: TopbarProps) {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const { data: notificationsData } = useSWR(null, fetcher, { 
    refreshInterval: 15000 
  });
  const unreadCount = notificationsData?.count ?? (Array.isArray(notificationsData?.results) ? notificationsData.results.length : 0);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = async () => {
    try {
      const refresh = getRefreshToken();
      if (refresh) {
        await authAPI.logout(refresh);
      }
    } catch {
      // ignore
    } finally {
      clearTokens();
      logout();
      router.replace("/login");
    }
  };

  const initials = getInitials(user?.first_name, user?.last_name, user?.username);

  return (
    <header
      className="flex-shrink-0 h-14 flex items-center gap-4 px-6 border-b border-gray-200 bg-white" // FIX[BUG 4]: updated gap and px
      id="topbar"
    >
      {/* Hamburger */}
      <button
        onClick={onMenuToggle}
        className="p-2 rounded-lg hover:bg-gray-100 transition-colors text-[var(--text-secondary)] lg:hidden flex-shrink-0"
        aria-label="Toggle menu"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Page Title */}
      <h2 className="text-[15px] font-semibold text-[var(--text-primary)] truncate flex-shrink-0 hidden sm:block"> {/* FIX[BUG 4]: added hidden sm:block */}
        {pageTitle}
      </h2>

      {/* Search — takes remaining space, separated from title */}
      <div className="flex-1 min-w-0 max-w-sm hidden md:block"> {/* FIX[BUG 4]: max-w-sm instead of max-w-xl */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-muted)]" />
          <input
            type="text"
            placeholder="Search clients, loans, applications..."
            className="w-full pl-9 pr-4 py-2 text-[13px] bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-lg outline-none focus:border-[var(--color-primary)] focus:ring-2 focus:ring-blue-100 transition-all placeholder:text-[var(--text-muted)]"
          />
        </div>
      </div>

      <div className="ml-auto flex items-center gap-3 flex-shrink-0"> {/* FIX[BUG 4]: added flex-shrink-0 */}
        {/* Notifications */}
        <Link
          href="/notifications"
          className="relative h-9 w-9 flex items-center justify-center rounded-full hover:bg-gray-100 text-gray-500 transition-colors"
          aria-label="Notifications"
        >
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <span className="absolute top-1.5 right-1.5 flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500 border-2 border-white"></span>
            </span>
          )}
        </Link>

        {/* User Avatar + Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setDropdownOpen((v) => !v)}
            className="flex items-center gap-2.5 pl-2 pr-3 py-1.5 rounded-xl hover:bg-gray-100 transition-colors"
            aria-expanded={dropdownOpen}
            aria-haspopup="true"
          >
            <div className="h-8 w-8 rounded-full flex items-center justify-center text-sm font-medium bg-blue-100 text-blue-700">
              {initials}
            </div>
            <div className="hidden md:flex items-center gap-1 text-sm">
              <p className="font-medium text-[var(--text-primary)] leading-tight">
                {user?.role_display}
              </p>
              <ChevronDown className="h-4 w-4 text-[var(--text-muted)]" />
            </div>
          </button>

          {dropdownOpen && (
            <div className="absolute right-0 top-full mt-2 w-52 bg-white rounded-xl shadow-lg border border-[var(--border-color)] py-1.5 z-50 animate-scale-in">
              {/* User info */}
              <div className="px-4 py-3 border-b border-[var(--border-color)]">
                <p className="text-[13px] font-semibold text-[var(--text-primary)]">
                  {user?.first_name || user?.username} {user?.last_name || ""}
                </p>
                <p className="text-[12px] text-[var(--text-muted)] truncate">{user?.email}</p>
              </div>

              <Link
                href="/profile"
                onClick={() => setDropdownOpen(false)}
                className="flex items-center gap-3 px-4 py-2.5 text-[13px] text-[var(--text-primary)] hover:bg-gray-50 transition-colors"
              >
                <User className="h-4 w-4 text-[var(--text-muted)]" />
                My Profile
              </Link>
              <Link
                href="/profile"
                onClick={() => setDropdownOpen(false)}
                className="flex items-center gap-3 px-4 py-2.5 text-[13px] text-[var(--text-primary)] hover:bg-gray-50 transition-colors"
              >
                <Settings className="h-4 w-4 text-[var(--text-muted)]" />
                Settings
              </Link>

              <div className="border-t border-[var(--border-color)] mt-1 pt-1">
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-3 w-full px-4 py-2.5 text-[13px] text-red-600 hover:bg-red-50 transition-colors"
                >
                  <LogOut className="h-4 w-4" />
                  Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
