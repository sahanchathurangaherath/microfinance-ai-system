"use client";

import { cn } from "@/lib/utils";
import { FolderSearch, AlertCircle, FileX, BellOff } from "lucide-react";
import Button from "./Button";
import type { ReactNode } from "react";

export type EmptyStateVariant = "no-data" | "no-results" | "error" | "no-notifications";

interface EmptyStateProps {
  variant?: EmptyStateVariant;
  title?: string;
  description?: string;
  icon?: ReactNode;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export default function EmptyState({
  variant = "no-data",
  title,
  description,
  icon,
  actionLabel,
  onAction,
  className,
}: EmptyStateProps) {
  const getDefaultContent = () => {
    switch (variant) {
      case "no-results":
        return {
          icon: <FolderSearch className="h-12 w-12 text-gray-300" />,
          title: "No results found",
          description: "We couldn't find any items matching your filters. Try adjusting them.",
        };
      case "error":
        return {
          icon: <AlertCircle className="h-12 w-12 text-red-300" />,
          title: "Something went wrong",
          description: "An error occurred while loading this data.",
        };
      case "no-notifications":
        return {
          icon: <BellOff className="h-12 w-12 text-gray-300" />,
          title: "All caught up!",
          description: "You have no new notifications right now.",
        };
      case "no-data":
      default:
        return {
          icon: <FileX className="h-12 w-12 text-gray-300" />,
          title: "No data available",
          description: "There are currently no items to display here.",
        };
    }
  };

  const defaults = getDefaultContent();
  const displayIcon = icon || defaults.icon;
  const displayTitle = title || defaults.title;
  const displayDesc = description || defaults.description;

  return (
    <div className={cn("flex flex-col items-center justify-center py-16 px-4 text-center animate-fadeIn", className)}>
      <div className="mb-4 bg-gray-50 rounded-full p-4 border border-gray-100 shadow-sm">
        {displayIcon}
      </div>
      <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-1">
        {displayTitle}
      </h3>
      <p className="text-sm text-[var(--text-muted)] max-w-sm mb-6">
        {displayDesc}
      </p>
      {actionLabel && onAction && (
        <Button onClick={onAction} variant="secondary">
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
