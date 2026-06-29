'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';

/**
 * /dashboard root — redirects user to their role-specific dashboard
 */
export default function DashboardRootPage() {
  const router = useRouter();

  useEffect(() => {
    const role = Cookies.get('user_role');
    const routeMap: Record<string, string> = {
      admin: '/dashboard/admin',
      loan_officer: '/dashboard/loan-officer',
      risk_analyst: '/dashboard/risk-analyst',
      branch_manager: '/dashboard/branch-manager',
      credit_committee: '/dashboard/credit-committee',
      collections_officer: '/dashboard/collections',
      compliance_officer: '/dashboard/compliance',
      finance_staff: '/dashboard/finance',
    };
    if (role && routeMap[role]) {
      router.replace(routeMap[role]);
    } else {
      router.replace('/dashboard/admin');
    }
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-50">
      <div className="w-8 h-8 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
    </div>
  );
}
