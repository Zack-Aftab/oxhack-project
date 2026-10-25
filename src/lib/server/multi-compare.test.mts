import {test} from "node:test";
import assert from "node:assert/strict";
import {CATEGORY_SPECIALTY,SPECIALTIES,initialMultiResponse,recommendMultiple,validateMultiRequest,type MultiCatalogData} from "./multi-compare.ts";
import type {MultiCompareRequest} from "../../../contracts/multi-compare.ts";
const request=():MultiCompareRequest=>({complaintCategories:["fracture_sprain_or_dislocation","chest_pain_or_heart_symptoms"],urgencyRating:4.25,likelyBedOccupancy:false,isEmergency:false,simulationAt:"2026-09-25T18:00:00+01:00",originId:"london-demo",travelMode:"demo"});
const catalog=():MultiCatalogData=>({categorySpecialties:CATEGORY_SPECIALTY,notice:"Invented demo coverage",measuredStart:"2026-09-21T00:00:00+01:00",measuredEndExclusive:"2026-10-21T00:00:00+01:00",hospitals:[
 {hospitalId:"H001",name:"Full demo hub",supported:Object.fromEntries(SPECIALTIES.map(s=>[s,true])),onDuty:Object.fromEntries(SPECIALTIES.map(s=>[s,1])),estimates:{"4":{mean:80,count:30},"10":{mean:10,count:30}},pooledEstimate:{mean:60,count:300}},
 {hospitalId:"H002",name:"Demo ortho site",supported:Object.fromEntries(SPECIALTIES.map(s=>[s,s==="orthopaedics"||s==="emergency_medicine"])),onDuty:Object.fromEntries(SPECIALTIES.map(s=>[s,s==="orthopaedics"||s==="emergency_medicine"?1:0])),estimates:{"4":{mean:10,count:20}},pooledEstimate:{mean:30,count:200}},
]});
test("all categories must be covered; an orthopaedic-only site cannot win a two-category request",()=>{
 const r=recommendMultiple(request(),catalog());assert.deepEqual(r.hospitals.map(h=>h.hospitalId),["H001"]);assert.deepEqual(r.excludedHospitals[0]?.missingSpecialties,["cardiology"]);
 const one=request();one.complaintCategories=["fracture_sprain_or_dislocation"];
 assert.deepEqual(recommendMultiple(one,catalog()).hospitals.map(h=>h.hospitalId),["H002","H001"]);
});
test("unknown requires manual categorisation, and emergency overrides category confirmation",()=>{
 const x=request();x.complaintCategories=["unknown"];
 assert.equal(initialMultiResponse(x as unknown as Record<string,unknown>)?.action,"self_categorise");
 x.urgencyRating=null;assert.equal(initialMultiResponse(x as unknown as Record<string,unknown>)?.action,"self_categorise");
 assert.equal(initialMultiResponse({isEmergency:true})?.action,"call_999");
});
test("floating urgency is accepted; bed need forces 10 without automatically calling 999",()=>{
 assert.equal(validateMultiRequest(request()).urgencyRating,4.25);
 const x=request();x.likelyBedOccupancy=true;
 const r=recommendMultiple(x,catalog());assert.equal(r.effectiveUrgencyRating,10);assert.equal(r.action,"recommendations");assert.equal(r.hospitals[0]?.estimatedWaitMinutes,10);
});
test("incomplete coverage or loss of the full staffed hub is an error, not an invented match",()=>{
 const data=catalog();delete data.hospitals[0]!.supported.cardiology;assert.throws(()=>recommendMultiple(request(),data));
});
test("bad categories, mixed unknown, invalid urgency and timezone-free dates are rejected",()=>{
 for(const change of [{complaintCategories:["invented"]},{complaintCategories:["unknown","cuts_or_wounds"]},{urgencyRating:NaN},{urgencyRating:10.1},{simulationAt:"2026-09-25T18:00:00"}])assert.throws(()=>validateMultiRequest({...request(),...change}));
 assert.equal(CATEGORY_SPECIALTY.unknown,"emergency_medicine");
});
