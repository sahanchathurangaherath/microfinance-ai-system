"use client";

import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
  lines?: number;
  circle?: boolean;
}

export default function Skeleton({
  className,
  lines = 1,
  circle = false,
}: SkeletonProps) {
  if (circle) {
    return (
      <div
        className={cn("rounded-full animate-shimmer", className)}
        style={{ aspectRatio: "1" }}
      />
    );
  }

  return (
    <div className="space-y-3">
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className={cn(
            "h-4 rounded-md animate-shimmer",
            i === lines - 1 && lines > 1 ? "w-3/4" : "w-full",
            className
          )}
        />
      ))}
    </div>
  );
}

export function TableSkeleton({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex gap-4 px-4 py-3">
        {Array.from({ length: cols }).map((_, i) => (
          <div key={i} className="h-3 rounded animate-shimmer flex-1" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4 px-4 py-3 border-t border-gray-100">
          {Array.from({ length: cols }).map((_, j) => (
            <div key={j} className="h-4 rounded animate-shimmer flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}
