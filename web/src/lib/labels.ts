import type { RecallSource, Severity } from "@/lib/api";

export const SOURCE_LABEL: Record<RecallSource, string> = {
  cpsc: "CPSC · Consumer products",
  fda: "FDA · Food, drugs, devices",
  nhtsa: "NHTSA · Vehicles",
};

export const SOURCE_SHORT: Record<RecallSource, string> = {
  cpsc: "CPSC",
  fda: "FDA",
  nhtsa: "NHTSA",
};

export const SEVERITY_LABEL: Record<Severity, string> = {
  critical: "Serious hazard",
  high: "High risk",
  medium: "Moderate risk",
  low: "Low risk",
};

export function formatDate(iso: string | null) {
  if (!iso) return "Date unknown";
  // Recall dates are calendar dates; format in UTC so they never shift a day.
  return new Date(`${iso}T00:00:00Z`).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  });
}
