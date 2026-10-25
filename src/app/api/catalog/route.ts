import type { ErrorResponse } from "../../../../contracts/queuecare";
import { loadCatalog } from "@/lib/server/catalog";
import { createSupabaseRead } from "@/lib/server/supabase-rest";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(): Promise<Response> {
  const headers = { "Cache-Control": "no-store" };
  try {
    const catalog = await loadCatalog(createSupabaseRead(process.env), process.env.SUPABASE_DATASET_ID || "month-v5");
    return Response.json(catalog, { headers });
  } catch {
    // Do not expose database details, credentials or raw provider errors.
    const error: ErrorResponse = { schemaVersion: "queuecare.v1", error: { code: "INTERNAL_ERROR", message: "Hospital catalog is unavailable. Check the server connection and try again." } };
    return Response.json(error, { status: 500, headers });
  }
}
