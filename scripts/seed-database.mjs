import { readFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
import assert from 'node:assert/strict';

export function validate(data) {
  assert.equal(data.dataset_metadata?.synthetic_data, true, 'Only synthetic demo data is supported');
  const hospitalIds = new Set();
  for (const table of ['hospitals', 'visits', 'staffing_snapshots']) {
    assert(Array.isArray(data[table]) && data[table].length, `${table} must be a nonempty array`);
    const key = { hospitals: 'hospital_id', visits: 'visit_id', staffing_snapshots: 'snapshot_id' }[table];
    const seen = new Set();
    for (const row of data[table]) {
      assert(typeof row[key] === 'string' && row[key], `${table}: missing ID`);
      assert(!seen.has(row[key]), `${table}: duplicate ID ${row[key]}`);
      seen.add(row[key]);
      if (table === 'hospitals') {
        hospitalIds.add(row.hospital_id);
        assert(Number.isFinite(row.latitude) && Math.abs(row.latitude) <= 90, 'Invalid latitude');
        assert(Number.isFinite(row.longitude) && Math.abs(row.longitude) <= 180, 'Invalid longitude');
      } else {
        assert(hospitalIds.has(row.hospital_id), `${table}: unknown hospital`);
      }
      if (table === 'visits') {
        for (const field of ['likely_bed_occupancy', 'clinician_urgent']) {
          assert(row[field] === undefined || row[field] === null || typeof row[field] === 'boolean', `${field} must be boolean or null`);
        }
        const a = row.wait_reception_to_doctor_referral_minutes;
        const b = row.wait_doctor_referral_to_diagnosis_minutes;
        assert(Number.isInteger(a) && a >= 0 && Number.isInteger(b) && b >= 0, 'Invalid wait');
        assert.equal(row.estimated_total_arrival_to_diagnosis_minutes, a + b, 'Wait total mismatch');
        const arrival = Date.parse(row.arrival_at);
        assert(Number.isFinite(arrival), 'Invalid arrival');
        assert.equal(Date.parse(row.referral_at), arrival + a * 60000, 'Referral time mismatch');
        assert.equal(Date.parse(row.diagnosis_at), arrival + (a + b) * 60000, 'Diagnosis time mismatch');
      }
      if (table === 'staffing_snapshots') {
        assert(Date.parse(row.staffing_window_end) > Date.parse(row.snapshot_at), 'Invalid snapshot window');
        for (const field of ['general_doctors_available', 'beds_available', 'patients_waiting_for_doctor_referral', 'patients_waiting_for_diagnosis', 'arrivals_during_next_4h']) {
          assert(Number.isInteger(row[field]) && row[field] >= 0, `Invalid ${field}`);
        }
        assert(row.specialty_doctors_available && !Array.isArray(row.specialty_doctors_available) && typeof row.specialty_doctors_available === 'object', 'Invalid specialty counts');
        assert(Object.values(row.specialty_doctors_available).every(n => Number.isInteger(n) && n >= 0), 'Invalid specialty count');
      }
    }
  }
  return Object.fromEntries(['hospitals', 'visits', 'staffing_snapshots'].map(t => [t, data[t].length]));
}

export async function seed(data, url, key, request = fetch) {
  validate(data); // Validate everything before the first write.
  const base = new URL(url);
  assert(base.protocol === 'https:' && base.hostname.endsWith('.supabase.co') && base.pathname === '/' && !base.username && !base.password && !base.search && !base.hash && !base.port, 'Use your HTTPS Supabase project URL');
  assert(key, 'SUPABASE_SECRET_KEY is required');
  for (const table of ['hospitals', 'visits', 'staffing_snapshots']) {
    const rows = data[table];
    for (let offset = 0; offset < rows.length; offset += 500) {
      const response = await request(new URL(`/rest/v1/${table}`, base), {
        method: 'POST',
        redirect: 'error',
        headers: { apikey: key, ...(key.startsWith('sb_secret_') ? {} : { Authorization: `Bearer ${key}` }), 'Content-Type': 'application/json', Prefer: 'resolution=merge-duplicates,return=minimal' },
        body: JSON.stringify(rows.slice(offset, offset + 500)),
      });
      if (!response.ok) {
        // Do not dump remote responses or authentication material.
        throw new Error(`${table} batch ${offset / 500 + 1} failed (HTTP ${response.status}). Check migration, project URL and server key. Earlier batches may be present; rerun safely after fixing.`);
      }
    }
    console.log(`Imported ${rows.length} ${table} records`);
  }
}

async function main() {
  const args = process.argv.slice(2);
  const file = args.find(a => !a.startsWith('--'));
  assert(file && args.every(a => a === file || a === '--validate'), 'Usage: node --env-file-if-exists=.env.local scripts/seed-database.mjs <dataset.json> [--validate]');
  const data = JSON.parse(await readFile(file, 'utf8'));
  console.log('Validated:', validate(data));
  if (!args.includes('--validate')) await seed(data, process.env.SUPABASE_URL, process.env.SUPABASE_SECRET_KEY);
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch(error => { console.error(error.message); process.exitCode = 1; });
}
