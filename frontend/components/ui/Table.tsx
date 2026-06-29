"use client";

import { cn } from "@/lib/utils";
import { TableSkeleton } from "./Skeleton";
import { FileSearch } from "lucide-react";
import ErrorState from "./ErrorState";
import EmptyState from "./EmptyState";

export interface Column<T = Record<string, unknown>> {
  id: string;
  header: string;
  accessor?: keyof T;
  cell?: (row: T) => React.ReactNode;
  className?: string;
}

interface TableProps<T = Record<string, unknown>> {
  columns: Column<T>[];
  data: T[];
  loading?: boolean;
  error?: any;
  onRetry?: () => void;
  emptyMessage?: string;
  className?: string;
}

export default function Table<T extends Record<string, unknown>>({
  columns,
  data,
  loading = false,
  error,
  onRetry,
  emptyMessage = "No data found",
  className,
}: TableProps<T>) {
  if (loading && !data?.length) {
    return <TableSkeleton rows={5} cols={columns.length} />;
  }

  if (error && !data?.length) {
    return (
      <div className={cn("w-full overflow-x-auto table-shell bg-white rounded-2xl border border-gray-200", className)}>
         <ErrorState 
            title="Failed to load data" 
            message={typeof error === 'string' ? error : error?.message || "An error occurred while loading this data."}
            onRetry={onRetry} 
         />
      </div>
    );
  }

  return (
    <div className={cn("w-full overflow-x-auto table-shell", className)}>
      <table className="w-full min-w-[720px] text-sm border-collapse">
        <thead className="sticky top-0 bg-white z-10 border-b border-gray-200">
          <tr>
            {columns.map((col) => (
              <th key={col.id} className={cn("text-left text-xs font-medium text-gray-500 uppercase tracking-wide px-4 py-3", col.className)}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="py-16 text-center">
                <EmptyState variant="no-data" description={emptyMessage} />
              </td>
            </tr>
          ) : (
            data.map((row, i) => (
              <tr key={i} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                {columns.map((col) => (
                  <td key={col.id} className={cn("px-4 py-3 text-sm", col.className)}>
                    {col.cell
                      ? col.cell(row)
                      : col.accessor
                      ? String(row[col.accessor] ?? "-")
                      : "-"}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
