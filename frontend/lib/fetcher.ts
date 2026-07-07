import api from "./api";

/**
 * SWR fetcher that uses the shared Axios instance.
 */
export async function fetcher<T = unknown>(url: string): Promise<T> {
  const response = await api.get(url);
  return response.data as T;
}

/**
 * Format number as LKR currency
 */
export function formatLKR(amount: number): string {
  return `LKR ${amount.toLocaleString('en-LK', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  })}`;
}

/**
 * Format date as readable string
 */
export function formatDate(dateStr: string): string {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}
