import assert from "node:assert/strict";
import { test } from "node:test";
import { loadCatalog, type SupabaseRead } from "./catalog.ts";
import { createSupabaseRead } from "./supabase-rest.ts";

const hospital = { hospital_id: "H001", name: "From database", address: "Database address", latitude: 51.5, longitude: -.1 };
const metadata = { synthetic_data: true, timezone: "Europe/London", notice: "Database synthetic notice", measured_start: "2026-09-21", measured_end_exclusive: "2026-10-21", category_specific_flag_probabilities: { fracture_sprain_or_dislocation: .05, unknown: .01 } };
function reader(hospitals: unknown = [hospital], meta: unknown = metadata): SupabaseRead {
  return async table => table === "hospitals" ? hospitals : [{ dataset_id: "month-v5", model_version: "resource_queue_month_v5", metadata: meta }];
}
test("catalog maps actual rows and configured categories, preserving the wire shape and inclusive dates", async () => {
  const result = await loadCatalog(reader());
  assert.equal(result.hospitals[0]?.name, "From database");
  assert.equal(result.notice, "Database synthetic notice");
  assert.equal(result.dateRange.end, "2026-10-20");
  assert.deepEqual(result.complaintCategories.map(c => c.id), ["fracture_sprain_or_dislocation", "unknown"]);
  assert.equal(result.defaultComparison.simulationAt, "2026-09-25T18:00:00+01:00");
  assert.equal(JSON.stringify(result).includes("category_specific_flag_probabilities"), false);
});
test("missing rows, corrupt category metadata and bad coordinates fail without fixture fallback", async () => {
  await assert.rejects(loadCatalog(reader([])));
  await assert.rejects(loadCatalog(reader([hospital], { ...metadata, category_specific_flag_probabilities: { made_up: .5 } })));
  await assert.rejects(loadCatalog(reader([{ ...hospital, latitude: 91 }])));
  await assert.rejects(loadCatalog(reader([hospital], { ...metadata, synthetic_data: false })));
});
test("database failures propagate instead of becoming sample responses", async () => {
  await assert.rejects(loadCatalog(async () => { throw new Error("unreachable"); }), /unreachable/);
});
test("REST transport sends secrets only in headers and disables redirects/caching", async () => {
  const request: typeof fetch = async (input, init) => {
    const url = new URL(String(input));
    assert.equal(url.pathname, "/rest/v1/hospitals");
    assert.equal(url.searchParams.get("select"), "hospital_id");
    assert.equal(url.href.includes("sb_secret_test"), false);
    assert.equal((init?.headers as Record<string, string>).apikey, "sb_secret_test");
    assert.equal((init?.headers as Record<string, string>).Authorization, undefined);
    assert.equal(init?.redirect, "error"); assert.equal(init?.cache, "no-store");
    return Response.json([hospital]);
  };
  const read = createSupabaseRead({ SUPABASE_URL: "https://example.supabase.co", SUPABASE_SECRET_KEY: "sb_secret_test" }, request);
  assert.deepEqual(await read("hospitals", { select: "hospital_id" }), [hospital]);
});
test("legacy role key works; missing credentials and HTTP denial fail", async () => {
  assert.throws(() => createSupabaseRead({ SUPABASE_URL: "https://example.supabase.co" }));
  const request: typeof fetch = async (_input, init) => {
    assert.equal((init?.headers as Record<string, string>).Authorization, "Bearer test-legacy");
    return new Response(null, { status: 403 });
  };
  const read = createSupabaseRead({ SUPABASE_URL: "https://example.supabase.co", SUPABASE_SERVICE_ROLE_KEY: "test-legacy" }, request);
  await assert.rejects(read("hospitals", {}), /403/);
});
