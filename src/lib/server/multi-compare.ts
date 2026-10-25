import type { MultiCompareRequest, MultiCompareResponse } from "../../../contracts/multi-compare.ts";
import type { ComplaintCategory, SpecialtyId } from "../../../contracts/queuecare.ts";

export const CATEGORY_SPECIALTY: Record<ComplaintCategory, SpecialtyId> = {
  fracture_sprain_or_dislocation: "orthopaedics", cuts_or_wounds: "wound_care_or_plastics",
  head_injury_or_neurological_symptoms: "neurology_or_neurosurgery", breathing_problems: "respiratory_medicine",
  chest_pain_or_heart_symptoms: "cardiology", abdominal_or_stomach_problems: "general_surgery_or_gastroenterology",
  other_or_uncategorised: "emergency_medicine", unknown: "emergency_medicine",
};
export const SPECIALTIES = [...new Set(Object.values(CATEGORY_SPECIALTY))];
export class MultiInputError extends Error {}
export function validateMultiRequest(value: unknown): MultiCompareRequest & { urgencyRating: number } {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new MultiInputError("Expected a JSON object");
  const x = value as Record<string, unknown>;
  if (!Array.isArray(x.complaintCategories) || !x.complaintCategories.length || x.complaintCategories.length>8 || !x.complaintCategories.every(c => typeof c==="string" && Object.hasOwn(CATEGORY_SPECIALTY,c)) || new Set(x.complaintCategories).size!==x.complaintCategories.length || (x.complaintCategories.includes("unknown") && x.complaintCategories.length>1)) throw new MultiInputError("Choose distinct supported categories; unknown must be resolved manually");
  if (typeof x.urgencyRating!=="number" || !Number.isFinite(x.urgencyRating) || x.urgencyRating<1 || x.urgencyRating>10 || typeof x.likelyBedOccupancy!=="boolean" || typeof x.isEmergency!=="boolean") throw new MultiInputError("Provide urgency 1–10 and explicit bed/emergency flags");
  if (typeof x.simulationAt!=="string" || !/(Z|[+-]\d\d:\d\d)$/.test(x.simulationAt) || !Number.isFinite(Date.parse(x.simulationAt)) || x.originId!=="london-demo" || x.travelMode!=="demo") throw new MultiInputError("Provide an offset-aware simulation time and the supported demo origin/travel mode");
  return x as unknown as MultiCompareRequest & { urgencyRating: number };
}
export function initialMultiResponse(body: Record<string, unknown>): MultiCompareResponse | null {
  const base = { schemaVersion: "queuecare.multi.v1" as const, syntheticData: true as const, notice: "Synthetic demo: category-specialist links, availability, urgency and waits are not verified clinical data.", hospitals: [], excludedHospitals: [] };
  // An explicitly supplied emergency flag takes precedence over any pending category confirmation.
  if (body.isEmergency===true) return { ...base, action: "call_999", message: "Possible medical emergency. Call 999 now. Do not wait for hospital comparisons.", effectiveUrgencyRating: 10, complaintCategories: [] };
  if(Array.isArray(body.complaintCategories) && body.complaintCategories.length===1 && body.complaintCategories[0]==="unknown") return { ...base, action:"self_categorise", message:"Select and confirm your categories manually before hospital recommendations.", effectiveUrgencyRating:null, complaintCategories:["unknown"] };
  validateMultiRequest(body);
  return null;
}
export interface MultiCatalogData {
  categorySpecialties: Record<ComplaintCategory, SpecialtyId>;
  notice: string;
  measuredStart: string;
  measuredEndExclusive: string;
  hospitals: { hospitalId: string; name: string; supported: Record<string, boolean>; onDuty: Record<string, number>; estimates: Record<string, { mean: number; count: number }>; pooledEstimate: { mean: number; count: number } }[];
}
const TRAVEL: Record<string, number>={ H001:24,H002:18,H003:12,H004:20,H005:32 };
export function recommendMultiple(req: MultiCompareRequest, data: MultiCatalogData): MultiCompareResponse {
  const early=initialMultiResponse(req as unknown as Record<string,unknown>);if(early)return early;
  const score=req.likelyBedOccupancy?10:validateMultiRequest(req).urgencyRating;
  const needs=[...new Set(req.complaintCategories.map(c=>data.categorySpecialties[c]))];
  const result: MultiCompareResponse={schemaVersion:"queuecare.multi.v1",syntheticData:true,notice:data.notice,action:"recommendations",message:"Only sites covering every confirmed category are ranked. Travel and waits are demo estimates.",effectiveUrgencyRating:score,complaintCategories:req.complaintCategories,hospitals:[],excludedHospitals:[]};
  // Missing entries are corrupt data, not an invented unknown/available state.
  if(!data.hospitals.some(h=>SPECIALTIES.every(s=>h.supported[s]===true && Number.isInteger(h.onDuty[s]) && (h.onDuty[s]??0)>0)))throw new Error("Complete staffed hub missing from dataset");
  for(const h of data.hospitals){
    for(const s of SPECIALTIES)if(typeof h.supported[s]!=="boolean" || !Number.isInteger(h.onDuty[s]) || (h.onDuty[s]??-1)<0)throw new Error("Incomplete explicit specialty catalog");
    const missing=needs.filter(s=>!h.supported[s] || (h.onDuty[s]??0)<1);
    if(missing.length){result.excludedHospitals.push({hospitalId:h.hospitalId,missingSpecialties:missing});continue;}
    const minutes=TRAVEL[h.hospitalId];if(minutes===undefined)throw new Error("Demo travel unavailable");
    const arrival=Date.parse(req.simulationAt)+minutes*60000;
    if(arrival<Date.parse(data.measuredStart) || arrival>=Date.parse(data.measuredEndExclusive))throw new MultiInputError("Arrival outside simulation coverage");
    const band=String(Math.floor(score));const selected=h.estimates[band];const estimate=selected??h.pooledEstimate;
    if(!Number.isFinite(estimate.mean)||estimate.mean<0||!Number.isInteger(estimate.count)||estimate.count<1)throw new Error("Wait estimate unavailable");
    result.hospitals.push({hospitalId:h.hospitalId,name:h.name,requiredSpecialties:needs,doctorsOnDuty:Object.fromEntries(needs.map(s=>[s,h.onDuty[s]])),travelMinutes:minutes,estimatedWaitMinutes:Math.ceil(estimate.mean),totalMinutes:minutes+Math.ceil(estimate.mean),estimateSource:selected?"simulation_urgency_band":"simulation_hospital_fallback",sampleCount:estimate.count});
  }
  result.hospitals.sort((a,b)=>a.totalMinutes-b.totalMinutes||a.hospitalId.localeCompare(b.hospitalId));
  return result;
}
