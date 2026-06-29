"use client";

import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import type { ReactNode } from "react";

interface StatCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon?: ReactNode;
  iconBg?: string;
  trend?: "up" | "down" | "neutral";
  progress?: number;
  className?: string;
  loading?: boolean;
}

export default function StatCard({
  title,
  value,
  change,
  changeLabel,
  icon,
  iconBg = "bg-blue-50",
  trend = "neutral",
  progress,
  className,
  loading = false,
}: StatCardProps) {
  const trendColors = {
    up: "text-emerald-600",
    down: "text-red-600",
    neutral: "text-gray-500",
  };

  const TrendIcon =
    trend === "up" ? TrendingUp : trend === "down" ? TrendingDown : Minus;

  if (loading) {
    return (
      <div className={cn("flex flex-col gap-3 p-4 sm:p-5 border border-gray-200 rounded-2xl bg-white shadow-sm", className)}>
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 space-y-2 flex-1">
            <div className="h-4 w-24 bg-gray-200 rounded animate-shimmer" />
            <div className="h-7 w-16 bg-gray-200 rounded animate-shimmer" />
          </div>
          {icon && (
            <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5", iconBg)}>
               <div className="w-5 h-5 bg-gray-200/50 rounded animate-shimmer" />
            </div>
          )}
        </div>
        <div className="flex items-center gap-1.5 mt-auto pt-2">
          <div className="h-3 w-16 bg-gray-200 rounded animate-shimmer" />
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col gap-3 p-4 sm:p-5 border border-gray-200 rounded-2xl bg-white shadow-sm", className)}> {/* FIX[BUG 5]: natural gap flow */}
      <div className="flex items-start justify-between gap-3"> {/* FIX[BUG 5]: items-start and gap-3 */}
        <div className="min-w-0"> {/* FIX[BUG 5]: added min-w-0 */}
          <p className="text-sm font-medium text-[var(--text-muted)] mb-1 truncate"> {/* FIX[BUG 5]: added truncate */}
            {title}
          </p>
          <p className="text-2xl font-bold text-[var(--text-primary)] tabular-nums"> {/* FIX[BUG 5]: adjusted text size and added tabular-nums */}
            {value}
          </p>
        </div>
        {icon && (
          <div
            className={cn(
              "w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5", // FIX[BUG 5]: rounded-xl, mt-0.5
              iconBg
            )}
          >
            {icon}
          </div>
        )}
      </div>

      {(change !== undefined || changeLabel) && (
        <div className="flex items-center gap-1.5">
          <TrendIcon className={cn("h-3.5 w-3.5 flex-shrink-0", trendColors[trend])} /> {/* FIX[BUG 5]: added flex-shrink-0 */}
          {change !== undefined && (
            <span className={cn("text-[13px] font-semibold", trendColors[trend])}>
              {change > 0 ? "+" : ""}
              {change}%
            </span>
          )}
          {changeLabel && (
            <span className="text-[12px] text-[var(--text-muted)]">
              {changeLabel}
            </span>
          )}
        </div>
      )}

      {progress !== undefined && (
        <div className="progress-bar mt-1"> {/* FIX[BUG 5]: replaced wrapper with mt-1 directly on progress-bar */}
          <div
            className="progress-bar-fill bg-[var(--color-primary)]"
            style={{ width: `${Math.min(progress, 100)}%` }}
          />
        </div>
      )}
    </div>
  );
}
