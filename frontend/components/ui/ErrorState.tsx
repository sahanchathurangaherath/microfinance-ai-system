"use client";

import { cn } from "@/lib/utils";
import { AlertTriangle, RefreshCcw } from "lucide-react";
import Button from "./Button";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  onBack?: () => void;
  className?: string;
}

export default function ErrorState({
  title = "Something went wrong",
  message = "An error occurred while trying to process your request. Please try again.",
  onRetry,
  onBack,
  className,
}: ErrorStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center py-12 px-4 text-center animate-fadeIn", className)}>
      <div className="mb-5 bg-red-50 rounded-full p-4 border border-red-100 shadow-sm">
        <AlertTriangle className="h-12 w-12 text-red-500" />
      </div>
      <h3 className="text-lg font-bold text-gray-900 mb-2">
        {title}
      </h3>
      <p className="text-sm text-gray-500 max-w-sm mb-8">
        {message}
      </p>
      <div className="flex flex-col sm:flex-row gap-3">
        {onRetry && (
          <Button onClick={onRetry} icon={<RefreshCcw className="h-4 w-4" />}>
            Try Again
          </Button>
        )}
        {onBack && (
          <Button onClick={onBack} variant="secondary">
            Go Back
          </Button>
        )}
      </div>
    </div>
  );
}
