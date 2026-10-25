import type { MultiCompareRequest, MultiCompareResponse } from "../../../contracts/multi-compare";
/** Separate opt-in adapter. Existing single-category callers remain unchanged. */
export async function compareMultiple(request:MultiCompareRequest):Promise<MultiCompareResponse>{
  const response=await fetch("/api/compare/multi",{method:"POST",headers:{"Content-Type":"application/json",accept:"application/json"},body:JSON.stringify(request)});
  const value=await response.json();
  if(!response.ok)throw new Error(value.error?.message||"Specialist comparison failed");
  if(value.schemaVersion!=="queuecare.multi.v1")throw new Error("Unexpected specialist comparison version");
  return value as MultiCompareResponse;
}
