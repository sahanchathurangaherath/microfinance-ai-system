"use client";

import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

interface CardProps {
  title?: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  padding?: boolean;
  noBorder?: boolean;
}

export default function Card({
  title,
  subtitle,
  action,
  children,
  className,
  padding = true,
  noBorder = false,
}: CardProps) {
  return (
    <div
      className={cn(
        "bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden",
        noBorder && "border-0 shadow-none",
        className
      )}
    >
      {(title || action) && (
        <div className="flex items-center justify-between gap-3 px-4 py-4 sm:px-6 border-b border-[var(--border-color)]">
          <div>
            {title && (
              <h3 className="text-[15px] font-semibold text-[var(--text-primary)]">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-[13px] text-[var(--text-muted)] mt-0.5">
                {subtitle}
              </p>
            )}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      <div className={cn(padding && "p-4 sm:p-6")}>{children}</div>
    </div>
  );
}
