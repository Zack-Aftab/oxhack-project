import type { SupabaseRead } from "./catalog.ts";

export function createSupabaseRead(
  env: Record<string, string | undefined>,
  request: typeof fetch = fetch,
): SupabaseRead {
  const url = new URL(env.SUPABASE_URL || "");
  const key = env.SUPABASE_SECRET_KEY || env.SUPABASE_SERVICE_ROLE_KEY;
  if (url.protocol !== "https:" || url.username || url.password || url.pathname !== "/" || url.search || url.hash || !key) throw new Error("Supabase server configuration missing or invalid");
  const headers: Record<string, string> = { apikey: key, accept: "application/json" };
  if (!key.startsWith("sb_secret_")) headers.Authorization = `Bearer ${key}`;
  return async (table, query) => {
    const target = new URL(`/rest/v1/${table}`, url);
    target.search = new URLSearchParams(query).toString();
    const response = await request(target, { headers, redirect: "error", cache: "no-store", signal: AbortSignal.timeout(10000) });
    if (!response.ok) throw new Error(`Supabase read failed (${response.status})`);
    return response.json();
  };
}
