import Cookies from 'js-cookie';

/**
 * SWR fetcher that attaches the access token from cookies.
 */
export async function fetcher<T = unknown>(url: string): Promise<T> {
  const accessToken = Cookies.get('access_token');

  const res = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    },
  });

  if (!res.ok) {
    const error = new Error(`API error: ${res.status} ${res.statusText}`);
    throw error;
  }

  return res.json();
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
