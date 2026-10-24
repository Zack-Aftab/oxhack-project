import { readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { parseArgs } from 'node:util';
import { gunzipSync } from 'node:zlib';
import { pathToFileURL } from 'node:url';
import assert from 'node:assert/strict';

const PROJECT = 'wlxljcobmhjmvnhjlvlk.supabase.co';
async function datasetBytes(path) {
  const bytes=await readFile(path);
  return path.endsWith('.gz') ? gunzipSync(bytes) : bytes;
}
const TABLES = ['hospitals', 'visits', 'staffing_snapshots'];
const KEYS = { hospitals: 'hospital_id', visits: 'visit_id', staffing_snapshots: 'snapshot_id', simulation_scenarios: 'scenario_id' };
export function validate(data) {
  const meta = data.dataset_metadata;
  assert(meta?.synthetic_data === true && meta.model_version === 'resource_queue_month_v5', 'Expected the selected monthly v5 synthetic dataset');
  assert.equal(meta.measured_days, 30, 'Expected 30 measured days');
  assert.equal(meta.runs, 5, 'Expected five runs');
  const start = Date.parse(`${meta.measured_start}T00:00:00+01:00`);
  const end = Date.parse(`${meta.measured_end_exclusive}T00:00:00+01:00`);
  assert.equal(end-start, 30*86400000);
  const hospitals = new Set();
  for (const table of TABLES) {
    assert(Array.isArray(data[table]) && data[table].length, `Missing ${table}`);
    const ids = new Set();
    for (const row of data[table]) {
      const id = row[KEYS[table]];
      assert(typeof id === 'string' && id && !ids.has(id), `${table}: missing/duplicate ID`);
      ids.add(id);
      if (table === 'hospitals') {
        hospitals.add(id);
        assert(typeof row.name === 'string' && typeof row.address === 'string');
        assert(Number.isFinite(row.latitude) && Math.abs(row.latitude)<=90);
        assert(Number.isFinite(row.longitude) && Math.abs(row.longitude)<=180);
      } else assert(hospitals.has(row.hospital_id), `${table}: invalid hospital`);
      if (table === 'visits') {
        const waits = row.simulation_waits_minutes;
        assert(Array.isArray(waits) && waits.length===5 && waits.every(w => Number.isFinite(w) && w>=0));
        assert.equal(row.simulation_run_count, 5);
        assert(Number.isInteger(row.mean_wait_to_first_doctor_minutes));
        assert.equal(row.mean_wait_to_first_doctor_minutes, Math.ceil(waits.reduce((a,b)=>a+b,0)/5));
        assert.equal(typeof row.likely_bed_occupancy,'boolean');
        const at = Date.parse(row.arrival_at);
        assert(at>=start && at<end, 'Visit outside measured month');
        assert.equal(Date.parse(row.mean_first_doctor_at)-at, row.mean_wait_to_first_doctor_minutes*60000);
        assert.equal(row.min_wait_to_first_doctor_minutes, Math.min(...waits));
        assert.equal(row.max_wait_to_first_doctor_minutes, Math.max(...waits));
        assert(Number.isFinite(row.wait_stddev_minutes) && row.wait_stddev_minutes>=0);
      }
      if (table === 'staffing_snapshots') {
        assert(Date.parse(row.snapshot_at)>=start && Date.parse(row.snapshot_at)<end);
        assert.equal(Date.parse(row.staffing_window_end)-Date.parse(row.snapshot_at),3600000);
        for (const name of ['general_doctors_available','triage_nurses_available','beds_available','observed_arrivals_last_hour']) assert(Number.isInteger(row[name]) && row[name]>=0, `Invalid ${name}`);
        for (const name of ['mean_general_doctors_free','mean_beds_free','mean_waiting_for_first_doctor','mean_waiting_for_triage']) assert(Number.isFinite(row[name]) && row[name]>=0, `Invalid ${name}`);
      }
    }
  }
  assert.equal(data.hospitals.length,5);
  assert.equal(data.staffing_snapshots.length,5*30*24);
  return Object.fromEntries(TABLES.map(t=>[t,data[t].length]));
}

function client() {
  const url = new URL(process.env.SUPABASE_URL);
  assert(url.protocol==='https:' && url.hostname===PROJECT && url.pathname==='/' && !url.username && !url.password && !url.search && !url.port, 'Unexpected Supabase project URL');
  const key=process.env.SUPABASE_SECRET_KEY;
  assert(key,'SUPABASE_SECRET_KEY missing');
  return async (path,options={}) => {
    const r=await fetch(new URL(`/rest/v1/${path}`,url),{
      ...options,redirect:'error',signal:AbortSignal.timeout(60000),
      headers:{apikey:key,...(key.startsWith('sb_secret_')?{}:{Authorization:`Bearer ${key}`}),...options.headers},
    });
    if(!r.ok) throw new Error(`Supabase ${path.split('?')[0]}: HTTP ${r.status}. Check migration and access; no response or credential values logged.`);
    return r;
  };
}
async function count(request,table) {
  const r=await request(`${table}?select=*&limit=1`,{method:'HEAD',headers:{Prefer:'count=exact'}});
  const value=Number(r.headers.get('content-range')?.split('/')[1]);
  assert(Number.isInteger(value) && value>=0,`Missing exact count for ${table}`);
  return value;
}
async function allRows(request,table,select='*') {
  const expected=await count(request,table);const rows=[];
  for(let offset=0;offset<expected;offset+=1000) {
    const r=await request(`${table}?select=${select}&order=${KEYS[table]}.asc&offset=${offset}&limit=1000`);
    const batch=await r.json();assert(Array.isArray(batch) && batch.length===Math.min(1000,expected-offset),'Incomplete database page');rows.push(...batch);
  }
  assert.equal(await count(request,table),expected,'Rows changed during backup/read; retry in a quiet window');
  assert.equal(new Set(rows.map(r=>r[KEYS[table]])).size,expected);
  return rows;
}
export function importRows(data,table) {
  const fields={
    hospitals:['hospital_id','name','address','latitude','longitude'],
    visits:['visit_id','hospital_id','arrival_at','complaint_category','likely_bed_occupancy','mean_wait_to_first_doctor_minutes','mean_first_doctor_at','simulation_waits_minutes','simulation_run_count','min_wait_to_first_doctor_minutes','max_wait_to_first_doctor_minutes','wait_stddev_minutes'],
    staffing_snapshots:['snapshot_id','hospital_id','snapshot_at','staffing_window_end','general_doctors_available','triage_nurses_available','beds_available','observed_arrivals_last_hour','mean_general_doctors_free','mean_beds_free','mean_waiting_for_first_doctor','mean_waiting_for_triage'],
  }[table];
  return data[table].map(row=>Object.fromEntries(fields.map(f=>[f,row[f]])));
}
export function assertRawWaits(actual, expected) {
  assert(Array.isArray(actual) && actual.length === expected.length, 'Wrong sample count');
  for (let i=0; i<expected.length; i++) {
    // PostgREST JSON may round double-precision samples. One nanominute tolerance
    // applies ONLY to raw samples; stored integer averages remain exact checks.
    assert(Number.isFinite(actual[i]) && Math.abs(actual[i]-expected[i]) <= 1e-9, `Raw wait sample ${i+1} mismatch`);
  }
}
async function main() {
  const {values}=parseArgs({options:{backup:{type:'string'},validate:{type:'string'},import:{type:'string'},verify:{type:'string'},summary:{type:'string'}}});
  assert.equal([values.backup,values.validate,values.import,values.verify].filter(Boolean).length,1,'Choose --backup PATH, --validate DATASET, --import DATASET --summary SUMMARY, or --verify DATASET --summary SUMMARY');
  if(values.validate) {const data=JSON.parse(await datasetBytes(values.validate));console.log('Validated:',validate(data));return;}
  const request=client();
  if(values.backup) {
    const tables={};for(const table of [...TABLES,'simulation_scenarios']) {tables[table]=await allRows(request,table);console.log(`Backed up ${table}: ${tables[table].length}`);}
    const payload=JSON.stringify({project:PROJECT,created_at:new Date().toISOString(),tables});
    await writeFile(values.backup,payload,{flag:'wx',mode:0o600});
    const check=await readFile(values.backup);
    assert.equal(createHash('sha256').update(check).digest('hex'),createHash('sha256').update(payload).digest('hex'));
    console.log(`Backup saved and read-back verified: ${values.backup}`);return;
  }
  assert(values.summary,'--summary is required for import/verification');
  const bytes=await datasetBytes(values.import ?? values.verify);const data=JSON.parse(bytes);const expected=validate(data);
  const summary=JSON.parse(await readFile(values.summary,'utf8'));
  assert.equal(summary.patients,expected.visits);assert.equal(summary.patient_runs,expected.visits*5);
  const marker=await request('simulation_datasets?select=dataset_id');await marker.json(); // Fails before writes if migration is absent.
  if(values.import) {
  for(const table of TABLES) {
    const allowed=new Set(data[table].map(r=>r[KEYS[table]]));
    for(const row of await allRows(request,table,KEYS[table])) assert(allowed.has(row[KEYS[table]]),`${table} has unrelated rows; refusing replacement`);
  }
  for(const table of TABLES) {
    const rows=importRows(data,table);
    for(let offset=0;offset<rows.length;offset+=500) {
      await request(`${table}?on_conflict=${KEYS[table]}`,{method:'POST',headers:{'Content-Type':'application/json',Prefer:'resolution=merge-duplicates,return=minimal'},body:JSON.stringify(rows.slice(offset,offset+500))});
    }
    assert.equal(await count(request,table),expected[table],`${table} count mismatch`);
    console.log(`Imported and counted ${table}: ${expected[table]}`);
  }
  } else {
    for(const table of TABLES) {
      assert.equal(await count(request,table),expected[table],`${table} count mismatch`);
      console.log(`Verified ${table}: ${expected[table]}`);
    }
  }
  for(const visit of [data.visits[0],data.visits[Math.floor(data.visits.length/2)],data.visits.at(-1)]) {
    const r=await request(`visits?visit_id=eq.${encodeURIComponent(visit.visit_id)}&select=mean_wait_to_first_doctor_minutes,likely_bed_occupancy,simulation_waits_minutes`);
    const [row]=await r.json();assert.equal(row.mean_wait_to_first_doctor_minutes,visit.mean_wait_to_first_doctor_minutes);
    assert.equal(row.likely_bed_occupancy,visit.likely_bed_occupancy);assertRawWaits(row.simulation_waits_minutes,visit.simulation_waits_minutes);
  }
  if(values.verify) {
    const expectedById=new Map(data.visits.map(row=>[row.visit_id,row]));
    const actualRows=await allRows(request,'visits','visit_id,mean_wait_to_first_doctor_minutes,likely_bed_occupancy,simulation_waits_minutes');
    for(const row of actualRows) {
      const expectedRow=expectedById.get(row.visit_id);assert(expectedRow,'Unknown visit ID');
      assert.equal(row.mean_wait_to_first_doctor_minutes,expectedRow.mean_wait_to_first_doctor_minutes);
      assert.equal(row.likely_bed_occupancy,expectedRow.likely_bed_occupancy);
      assertRawWaits(row.simulation_waits_minutes,expectedRow.simulation_waits_minutes);
    }
    console.log(`Verified all ${actualRows.length} stored integer averages, flags and five raw samples each`);
  }
  const metadata={dataset_id:'month-v5',model_version:data.dataset_metadata.model_version,metadata:{...data.dataset_metadata,dataset_file_sha256:createHash('sha256').update(bytes).digest('hex')},summary};
  await request('simulation_datasets?on_conflict=dataset_id',{method:'POST',headers:{'Content-Type':'application/json',Prefer:'resolution=merge-duplicates,return=minimal'},body:JSON.stringify([metadata])});
  console.log('Verified database samples and saved model metadata. Import complete.');
}
if(process.argv[1] && import.meta.url===pathToFileURL(process.argv[1]).href) main().catch(e=>{console.error(e.message);process.exitCode=1;});
