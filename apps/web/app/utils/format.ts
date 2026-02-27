import { format, parseISO } from "date-fns";

/**
 * Format a date string or Date object to a readable format
 */
export function formatDate(date: string | Date | null | undefined, formatStr: string = "MMM dd, yyyy"): string {
  if (!date) return "–";
  try {
    const dateObj = typeof date === "string" ? parseISO(date) : date;
    return format(dateObj, formatStr);
  } catch {
    return "–";
  }
}

/**
 * Format a number as currency
 */
export function formatCurrency(value: number | null | undefined, currency: string = "EUR"): string {
  if (value === null || value === undefined) return "–";
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency,
  }).format(value);
}

/**
 * Format a number with thousands separators
 */
export function formatNumber(value: number | null | undefined, decimals: number = 0): string {
  if (value === null || value === undefined) return "–";
  return value.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/**
 * Get badge color based on score value
 */
export function getScoreColor(score: number | null | undefined): {
  bg: string;
  border: string;
} {
  if (score === null || score === undefined) {
    return { bg: "rgba(255,255,255,0.02)", border: "var(--border)" };
  }
  
  if (score >= 80) {
    return { bg: "rgba(64,214,123,0.12)", border: "rgba(64,214,123,0.35)" };
  } else if (score >= 60) {
    return { bg: "rgba(255,183,64,0.12)", border: "rgba(255,183,64,0.35)" };
  } else {
    return { bg: "rgba(255,92,92,0.12)", border: "rgba(255,92,92,0.35)" };
  }
}

/**
 * Get status badge color
 */
export function getStatusColor(status: string): {
  bg: string;
  border: string;
} {
  const statusColors: Record<string, { bg: string; border: string }> = {
    ok: { bg: "rgba(64,214,123,0.12)", border: "rgba(64,214,123,0.35)" },
    success: { bg: "rgba(64,214,123,0.12)", border: "rgba(64,214,123,0.35)" },
    completed: { bg: "rgba(64,214,123,0.12)", border: "rgba(64,214,123,0.35)" },
    arrived: { bg: "rgba(64,214,123,0.12)", border: "rgba(64,214,123,0.35)" },
    warning: { bg: "rgba(255,183,64,0.12)", border: "rgba(255,183,64,0.35)" },
    pending: { bg: "rgba(255,183,64,0.12)", border: "rgba(255,183,64,0.35)" },
    in_progress: { bg: "rgba(87,134,255,0.12)", border: "rgba(87,134,255,0.35)" },
    in_transit: { bg: "rgba(87,134,255,0.12)", border: "rgba(87,134,255,0.35)" },
    error: { bg: "rgba(255,92,92,0.12)", border: "rgba(255,92,92,0.35)" },
    failed: { bg: "rgba(255,92,92,0.12)", border: "rgba(255,92,92,0.35)" },
    delayed: { bg: "rgba(255,92,92,0.12)", border: "rgba(255,92,92,0.35)" },
  };

  return statusColors[status.toLowerCase()] || { bg: "rgba(255,255,255,0.02)", border: "var(--border)" };
}

/**
 * Truncate text to a maximum length
 */
export function truncate(text: string | null | undefined, maxLength: number = 50): string {
  if (!text) return "–";
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + "...";
}

/**
 * Calculate percentage
 */
export function calculatePercentage(value: number, total: number): number {
  if (total === 0) return 0;
  return (value / total) * 100;
}

/**
 * Format percentage
 */
export function formatPercentage(value: number | null | undefined, decimals: number = 1): string {
  if (value === null || value === undefined) return "–";
  return `${value.toFixed(decimals)}%`;
}
