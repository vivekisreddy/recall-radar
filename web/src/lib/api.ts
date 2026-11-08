import "server-only";

import { connection } from "next/server";

/**
 * Typed client for the FastAPI backend. Server-side only: pages call these from Server
 * Components, so the API URL is never shipped to the browser and can change per deploy.
 * Types mirror backend/src/recall_radar/api/schemas.py — keep them in sync.
 */

export type RecallSource = "cpsc" | "fda" | "nhtsa";
export type Severity = "critical" | "high" | "medium" | "low";

export interface RecallSummary {
  id: string;
  source: RecallSource;
  source_id: string;
  title: string;
  hazard: string | null;
  category: string | null;
  severity: Severity | null;
  recall_date: string | null;
  image_url: string | null;
}

export interface Vehicle {
  make: string;
  model: string;
  model_year: number;
  applies_to: string | null;
}

export interface RecallProduct {
  brand: string | null;
  product_name: string | null;
  model_number: string | null;
  upc: string | null;
  lot_codes: unknown[] | null;
  date_ranges: unknown[] | null;
}

export interface RecallDetail extends RecallSummary {
  event_id: string | null;
  remedy: string | null;
  url: string | null;
  products: RecallProduct[];
  vehicles: Vehicle[];
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface Stats {
  total: number;
  by_source: { source: RecallSource; recalls: number }[];
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function apiFetch<T>(path: string, params?: Record<string, string | number | undefined>) {
  await connection(); // read API_URL at request time, not frozen at build time
  const base = process.env.API_URL ?? "http://localhost:8000";
  const url = new URL(path, base);
  for (const [key, value] of Object.entries(params ?? {})) {
    if (value !== undefined) url.searchParams.set(key, String(value));
  }
  const res = await fetch(url, { headers: { Accept: "application/json" } });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(res.status, body?.error?.message ?? res.statusText);
  }
  return (await res.json()) as T;
}

export const getRecalls = (opts: { source?: RecallSource; limit?: number; offset?: number } = {}) =>
  apiFetch<Page<RecallSummary>>("/api/v1/recalls", opts);

export const getRecall = (id: string) => apiFetch<RecallDetail>(`/api/v1/recalls/${id}`);

export const getStats = () => apiFetch<Stats>("/api/v1/recalls/stats");
