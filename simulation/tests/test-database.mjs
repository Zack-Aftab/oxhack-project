import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { gunzipSync } from 'node:zlib';
import { validate, importRows } from '../database.mjs';
const data=JSON.parse(gunzipSync(await readFile(new URL('../results/month-v5/dataset.json.gz',import.meta.url))));
test('selected monthly dataset has valid identities, five samples, integer means and hourly snapshots',()=>{
  assert.deepEqual(validate(data),{hospitals:5,visits:68705,staffing_snapshots:3600});
});
test('a wrong mean or missing flag is rejected before any import',()=>{
  const row=data.visits[0];const mean=row.mean_wait_to_first_doctor_minutes;const flag=row.likely_bed_occupancy;
  try {row.mean_wait_to_first_doctor_minutes=mean+1;assert.throws(()=>validate(data));row.mean_wait_to_first_doctor_minutes=mean;delete row.likely_bed_occupancy;assert.throws(()=>validate(data));}
  finally {row.mean_wait_to_first_doctor_minutes=mean;row.likely_bed_occupancy=flag;}
});
test('unknown hospital references are rejected',()=>{
  const row=data.visits[0];const id=row.hospital_id;
  try {row.hospital_id='missing';assert.throws(()=>validate(data));} finally {row.hospital_id=id;}
});
test('database mapping retains samples and excludes unmodelled specialty fields',()=>{
  const row=importRows(data,'visits')[0];assert.deepEqual(row.simulation_waits_minutes,data.visits[0].simulation_waits_minutes);
  assert.equal(Object.hasOwn(row,'wait_doctor_referral_to_diagnosis_minutes'),false);
  const snap=importRows(data,'staffing_snapshots')[0];assert.equal(Object.hasOwn(snap,'specialty_doctors_available'),false);assert.equal(Object.hasOwn(snap,'mean_waiting_for_specialist'),false);
});
