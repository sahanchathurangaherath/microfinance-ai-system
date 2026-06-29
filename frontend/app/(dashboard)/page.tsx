"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/store";
import { ROLE_HOME_PAGES } from "@/lib/permissions";
import Spinner from "@/components/ui/Spinner";

export default function DashboardRedirectPage() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);

  useEffect(() => {
    if (user?.role) {
      const home = ROLE_HOME_PAGES[user.role] || "/login";
      router.replace(home);
    }
  }, [user, router]);

  return (
    <div className="flex items-center justify-center h-64">
      <Spinner size="lg" />
    </div>
  );
}
