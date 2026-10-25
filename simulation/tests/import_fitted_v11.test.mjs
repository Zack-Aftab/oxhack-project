import test from 'node:test';import assert from 'node:assert/strict';import {readFile} from 'node:fs/promises';import {gunzipSync} from 'node:zlib';import {createImportRows,uploadAndActivate} from '../import_fitted_v11.mjs';
const data=JSON.parse(gunzipSync(await readFile(new URL('../results/fitted-v11/dataset.json.gz',import.meta.url))));const rows=createImportRows(data.visits);const env={SUPABASE_URL:'https://wlxljcobmhjmvnhjlvlk.supabase.co',SUPABASE_SECRET_KEY:'test-only-placeholder'};
test('prepares every source row with exact timestamp microseconds and null emergency waits',()=>{
 assert.equal(rows.length,67676);assert.equal(new Set(rows.map(r=>r.visit_sequence)).size,67676);
 for(let i=0;i<data.visits.length;i++){
  const v=data.visits[i],r=rows[i];const fraction=(v.arrival_at.match(/\.(\d+)/)?.[1]??'').padEnd(6,'0');
  assert.equal(r.arrival_epoch_microseconds,`${Date.parse(v.arrival_at)}${fraction.slice(3,6)}`);
  assert.equal(r.estimated_wait_to_first_doctor_minutes,v.is_emergency?null:Math.ceil(v.fitted_demo_wait_minutes));
 }
});
test('denied credentials stop before any write',async()=>{
 const methods=[];await assert.rejects(uploadAndActivate(rows,{env,request:async(_url,init)=>{methods.push(init.method??'GET');return new Response('{}',{status:401});}}),/no rows were written/);assert.deepEqual(methods,['GET','GET']);
});
test('a failed staging batch never activates the active dataset',async()=>{
 let posts=0;let activated=false;await assert.rejects(uploadAndActivate(rows,{env,request:async(url,init)=>{
  if(url.pathname.endsWith('/hospitals'))return Response.json([{hospital_id:'H001'}]);
  if(url.pathname.includes('/rpc/')){activated=true;return Response.json({});}
  if(init.method==='POST'){posts++;return new Response(null,{status:503});}
  return Response.json([]);
 }}),/active dataset was not switched/);assert.equal(posts,1);assert.equal(activated,false);
});
test('successful batches activate only after all 67676 records upload',async()=>{
 let uploaded=0;let calls=0;const result=await uploadAndActivate(rows,{env,request:async(url,init)=>{
  if(url.pathname.endsWith('/hospitals'))return Response.json([{hospital_id:'H001'}]);
  if(url.pathname.includes('/rpc/')){assert.equal(uploaded,67676);return Response.json({dataset_id:'fitted-v11',hospital_patients:67473,emergency_exits:203,fitted_mean_minutes:120,fitted_median_minutes:100});}
  if(init.method==='POST'){uploaded+=JSON.parse(init.body).length;calls++;return new Response(null,{status:201});}
  return Response.json([]);
 }});assert.equal(result.hospital_patients,67473);assert.equal(calls,68);
});
