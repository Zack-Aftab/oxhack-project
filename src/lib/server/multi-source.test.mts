import {test} from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {loadMultiSource} from "./multi-source.ts";
import {initialMultiResponse,recommendMultiple} from "./multi-compare.ts";
import type {SupabaseRead} from "./catalog.ts";
import type {MultiCompareRequest} from "../../../contracts/multi-compare.ts";
const metadata=JSON.parse(readFileSync(new URL('../../../simulation/results/specialist-v7/api-metadata.json',import.meta.url),'utf8'));
const inputData=JSON.parse(readFileSync(new URL("../../../simulation/input.json",import.meta.url),"utf8")) as {hospitals:{hospital_id:string;name:string}[]};
const summary=JSON.parse(readFileSync(new URL('../../../simulation/results/specialist-v7/summary.json',import.meta.url),'utf8')) as {profiles:Record<string,{support:Record<string,boolean>;specialist_doctors_on_duty:Record<string,number>;general_doctors_by_four_hour_block:number[]}>};
function database():SupabaseRead{
 return async table=>{
  if(table==="category_specialties")return Object.entries(metadata.category_mapping as Record<string,string>).map(([category_id,specialty_id])=>({category_id,specialty_id,requires_manual_selection:category_id==="unknown"}));
  if(table==="hospitals")return inputData.hospitals.map(h=>({hospital_id:h.hospital_id,name:h.name}));
  if(table==="simulation_datasets")return [{metadata}];
  if(table==="hospital_specialties")return Object.entries(summary.profiles).flatMap(([h,p])=>Object.entries(p.support).map(([s,supported])=>({hospital_id:h,specialty_id:s,supported})));
  if(table==="specialist_staffing")return Object.entries(summary.profiles).flatMap(([h,p])=>[3,4].flatMap(block=>Object.keys(p.support).map(s=>({hospital_id:h,specialty_id:s,shift_start:`2026-09-25T${block*4}:00:00+01:00`,shift_end:`2026-09-25T${(block+1)*4}:00:00+01:00`,doctors_on_duty:s==="emergency_medicine"?p.general_doctors_by_four_hour_block[block]:p.specialist_doctors_on_duty[s]}))));
  throw new Error('unexpected table');
 };
}
test("source selects staffing at arrival after a shift boundary, and filters every required category",async()=>{
 const at="2026-09-25T15:50:00+01:00";const data=await loadMultiSource(database(),at);
 const hub=data.hospitals.find(h=>h.hospitalId==="H001");assert.equal(hub?.onDuty.emergency_medicine,summary.profiles.H001?.general_doctors_by_four_hour_block[4]);
 const req:MultiCompareRequest={complaintCategories:["fracture_sprain_or_dislocation","chest_pain_or_heart_symptoms"],urgencyRating:4.25,likelyBedOccupancy:false,isEmergency:false,simulationAt:at,originId:"london-demo",travelMode:"demo"};
 assert.deepEqual(recommendMultiple(req,data).hospitals.map(h=>h.hospitalId),["H001"]);
});
test("out-of-period arrivals and a database denial do not fall back to profile fixtures",async()=>{
 await assert.rejects(loadMultiSource(database(),"2027-01-01T00:00:00Z"));
 await assert.rejects(loadMultiSource(async()=>{throw new Error('read denied');},"2026-09-25T15:50:00+01:00"),/read denied/);
});

test("committed multi-category, bed, manual and emergency examples match the actual model contract",async()=>{
 for(const name of ["multi","bed-max","manual","emergency"]){
  const request=JSON.parse(readFileSync(new URL(`../../../fixtures/specialist-v7/${name}.request.json`,import.meta.url),"utf8")) as MultiCompareRequest;
  const expected=JSON.parse(readFileSync(new URL(`../../../fixtures/specialist-v7/${name}.response.json`,import.meta.url),"utf8"));
  const actual=initialMultiResponse(request as unknown as Record<string,unknown>)??recommendMultiple(request,await loadMultiSource(database(),request.simulationAt));
  assert.deepEqual(actual,expected);
 }
});
