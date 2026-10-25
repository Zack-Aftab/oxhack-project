#!/usr/bin/env node
/** Server-key batch import after SUPABASE_SMALL_SETUP.sql. Never logs credentials. */
import {readFile} from 'node:fs/promises';
import {gunzipSync} from 'node:zlib';
import {fileURLToPath,pathToFileURL} from 'node:url';
const HOST='wlxljcobmhjmvnhjlvlk.supabase.co';
const CATEGORIES=['fracture_sprain_or_dislocation','cuts_or_wounds','head_injury_or_neurological_symptoms','breathing_problems','chest_pain_or_heart_symptoms','abdominal_or_stomach_problems','other_or_uncategorised','unknown'];
export class SafeImportError extends Error {}
export function createImportRows(visits){
 return visits.map(v=>{
  const fraction=(v.arrival_at.match(/\.(\d+)/)?.[1]??'').padEnd(6,'0');
  const micros=(BigInt(Date.parse(v.arrival_at))*1000n+BigInt(fraction.slice(3,6))).toString();
  const initial=CATEGORIES.indexOf(v.initial_category);
  if(initial<0||v.complaint_categories.some(c=>!CATEGORIES.includes(c)||c==='unknown'))throw new SafeImportError('Unexpected category in source dataset.');
  return {origin_code:Number(v.origin_hospital_id.slice(1)),destination_code:v.hospital_id?Number(v.hospital_id.slice(1)):0,arrival_epoch_microseconds:micros,visit_sequence:Number(v.visit_id.split('-').at(-1)),category_mask:v.complaint_categories.reduce((mask,c)=>mask|(1<<CATEGORIES.indexOf(c)),0),initial_category_index:initial,pain_score:v.pain_score,urgency_rating:v.urgency_rating,flags:Number(v.likely_bed_occupancy)+2*Number(v.is_emergency)+4*Number(v.manual_category_confirmation),raw_queue_wait_minutes:v.raw_queue_wait_minutes,fitted_demo_wait_minutes:v.fitted_demo_wait_minutes,estimated_wait_to_first_doctor_minutes:v.estimated_wait_to_first_doctor_minutes};
 });
}
export async function uploadAndActivate(rows,{env=process.env,request=fetch,progress=()=>{},batchSize=1000}={}){
 const url=new URL(env.SUPABASE_URL||'https://invalid.local');const key=env.SUPABASE_SECRET_KEY||env.SUPABASE_SERVICE_ROLE_KEY;
 if(url.protocol!=='https:'||url.hostname!==HOST||url.username||url.password||!key)throw new SafeImportError('Set the existing Supabase project URL and server-side secret securely in environment settings.');
 if(rows.length!==67676||new Set(rows.map(r=>r.visit_sequence)).size!==67676)throw new SafeImportError('The import must contain exactly 67676 unique generated records.');
 const headers={apikey:key,'Content-Type':'application/json'};
 // API-key-only is the supported path for proxy-bound sb_secret keys. Try bearer as
 // a compatibility path only when the initial project read is denied/empty.
 async function send(path,init={}){return request(new URL(path,url),{...init,headers:{...headers,...init.headers},redirect:'error',signal:AbortSignal.timeout(30000)});}
 let check=await send('/rest/v1/hospitals?select=hospital_id&limit=1');let count=check.ok?(await check.json()).length:0;
 if(!check.ok||!count){headers.Authorization=`Bearer ${key}`;check=await send('/rest/v1/hospitals?select=hospital_id&limit=1');count=check.ok?(await check.json()).length:0;}
 if(!check.ok||!count)throw new SafeImportError(`Supabase server access is unavailable (HTTP ${check.status}). Update the saved secret; no rows were written.`);
 const setup=await send('/rest/v1/demo_fitted_v11_import?select=visit_sequence&limit=1');
 if(!setup.ok)throw new SafeImportError(`Import setup is unavailable (HTTP ${setup.status}). Run SUPABASE_SMALL_SETUP.sql first; no rows were written.`);
 await setup.arrayBuffer();
 for(let offset=0;offset<rows.length;offset+=batchSize){
  const response=await send('/rest/v1/demo_fitted_v11_import?on_conflict=visit_sequence',{method:'POST',headers:{Prefer:'resolution=merge-duplicates,return=minimal'},body:JSON.stringify(rows.slice(offset,offset+batchSize))});
  if(!response.ok)throw new SafeImportError(`Batch upload failed (HTTP ${response.status}) after ${offset} rows. The active dataset was not switched; the upload can be resumed safely.`);
  await response.arrayBuffer();progress(Math.min(offset+batchSize,rows.length),rows.length);
 }
 const activated=await send('/rest/v1/rpc/demo_activate_fitted_v11',{method:'POST',body:'{}'});
 if(!activated.ok)throw new SafeImportError(`Activation was not confirmed (HTTP ${activated.status}). Do not assume the database changed; inspect the verification queries before retrying.`);
 const result=await activated.json();
 if(result.dataset_id!=='fitted-v11'||result.hospital_patients!==67473||result.emergency_exits!==203||Math.abs(result.fitted_mean_minutes-120)>1e-6||result.fitted_median_minutes!==100)throw new SafeImportError('Activation returned unexpected verification statistics; inspect Supabase before proceeding.');
 return result;
}
async function main(){
 const file=new URL('./results/fitted-v11/dataset.json.gz',import.meta.url);const data=JSON.parse(gunzipSync(await readFile(file)));const rows=createImportRows(data.visits);
 if(process.argv.includes('--dry-run')){console.log(JSON.stringify({prepared_records:rows.length,unique_sequences:new Set(rows.map(r=>r.visit_sequence)).size,network_requests:0}));return;}
 if(!process.argv.includes('--apply'))throw new SafeImportError('Use --dry-run to inspect preparation or --apply to upload and activate the authorized dataset.');
 const result=await uploadAndActivate(rows,{progress:(count,total)=>{if(count%10000===0||count===total)console.log(`Uploaded ${count}/${total} staging rows`);}});console.log(JSON.stringify(result,null,2));
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href)main().catch(error=>{console.error(error instanceof SafeImportError?error.message:'Import stopped due to a connection or configuration error. No credential details were logged.');process.exitCode=1;});
