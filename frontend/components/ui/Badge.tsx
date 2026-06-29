"use client";

import { cn, getStatusColor, getStatusBgColor, capitalizeFirst } from "@/lib/utils";

interface BadgeProps {
  status: string;
  children?: React.ReactNode;
  className?: string;
}

export default function Badge({ status, children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center whitespace-nowrap px-2.5 py-1 rounded-full text-[11px] font-bold",
        getStatusBgColor(status),
        getStatusColor(status),
        className
      )}
    >
      {children || capitalizeFirst(status.toLowerCase().replace(/_/g, " "))}
    </span>
  );
}
