import test from 'node:test';
import assert from 'node:assert/strict';
import { seed, validate } from '../scripts/seed-database.mjs';
const fixture = () => ({
  dataset_metadata: { synthetic_data: true },
  hospitals: [{ hospital_id: 'H1', name: 'Demo', latitude: 51, longitude: 0 }],
  visits: [{ visit_id: 'V1', hospital_id: 'H1', arrival_at: '2026-10-01T00:00:00Z', referral_at: '2026-10-01T00:10:00Z', diagnosis_at: '2026-10-01T00:30:00Z', wait_reception_to_doctor_referral_minutes: 10, wait_doctor_referral_to_diagnosis_minutes: 20, estimated_total_arrival_to_diagnosis_minutes: 30 }],
  staffing_snapshots: [{ snapshot_id: 'S1', hospital_id: 'H1', snapshot_at: '2026-10-01T00:00:00Z', staffing_window_end: '2026-10-01T04:00:00Z', general_doctors_available: 2, beds_available: 3, patients_waiting_for_doctor_referral: 4, patients_waiting_for_diagnosis: 5, arrivals_during_next_4h: 6, specialty_doctors_available: { orthopaedics: 1 } }],
});
test('rejects duplicate IDs, dangling hospitals, inconsistent times and negative specialty counts', () => {
  for (const mutate of [d => d.visits.push(d.visits[0]), d => d.visits[0].hospital_id = 'missing', d => d.visits[0].diagnosis_at = d.visits[0].arrival_at, d => d.staffing_snapshots[0].specialty_doctors_available.orthopaedics = -1]) {
    const d = fixture(); mutate(d); assert.throws(() => validate(d));
  }
});
test('validates all data before making any write', async () => {
  const d = fixture(); d.staffing_snapshots[0].beds_available = -1;
  let calls = 0;
  await assert.rejects(seed(d, 'https://demo.supabase.co', 'test', async () => { calls++; }));
  assert.equal(calls, 0);
});
test('imports parents first, batches 500 rows, and uses upsert', async () => {
  const d = fixture(); d.visits = Array.from({ length: 501 }, (_, i) => ({ ...d.visits[0], visit_id: `V${i}` }));
  const calls = [];
  await seed(d, 'https://demo.supabase.co', 'test', async (url, options) => {
    calls.push([url.pathname, JSON.parse(options.body).length]);
    assert.equal(options.headers.Prefer, 'resolution=merge-duplicates,return=minimal');
    assert.equal(options.redirect, 'error');
    return { ok: true };
  });
  assert.deepEqual(calls, [['/rest/v1/hospitals', 1], ['/rest/v1/visits', 500], ['/rest/v1/visits', 1], ['/rest/v1/staffing_snapshots', 1]]);
});
test('stops on a failed batch without exposing the response', async () => {
  let calls = 0;
  await assert.rejects(seed(fixture(), 'https://demo.supabase.co', 'test', async () => { calls++; return { ok: false, status: 401 }; }), /HTTP 401/);
  assert.equal(calls, 1);
});

test('accepts boolean, unknown and absent clinical labels; rejects string/number substitutes', () => {
  for (const field of ['likely_bed_occupancy', 'clinician_urgent']) {
    for (const value of [true, false, null, undefined]) {
      const d = fixture(); d.visits[0][field] = value;
      assert.doesNotThrow(() => validate(d));
    }
    for (const value of ['true', 'false', 0, 1, {}, []]) {
      const d = fixture(); d.visits[0][field] = value;
      assert.throws(() => validate(d), /must be boolean or null/);
    }
  }
});

test('preserves the bed flag in imports and leaves absent historical labels omitted', async () => {
  const d = fixture();
  d.visits.push({ ...d.visits[0], visit_id: 'V2', likely_bed_occupancy: true });
  await seed(d, 'https://demo.supabase.co', 'test', async (url, options) => {
    if (url.pathname.endsWith('/visits')) {
      const rows = JSON.parse(options.body);
      assert.equal(Object.hasOwn(rows[0], 'likely_bed_occupancy'), false);
      assert.equal(rows[1].likely_bed_occupancy, true);
    }
    return { ok: true };
  });
});
