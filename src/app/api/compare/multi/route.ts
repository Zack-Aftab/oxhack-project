import { initialMultiResponse, MultiInputError, recommendMultiple, validateMultiRequest } from "@/lib/server/multi-compare";
import { loadMultiSource } from "@/lib/server/multi-source";
import { createSupabaseRead } from "@/lib/server/supabase-rest";
export const runtime="nodejs";
export const dynamic="force-dynamic";
export async function POST(request:Request):Promise<Response>{
  const headers={"Cache-Control":"no-store"};
  try{
    let body:unknown;try{body=await request.json();}catch{throw new MultiInputError("Expected JSON");}
    if(!body||typeof body!=="object"||Array.isArray(body))throw new MultiInputError("Expected a JSON object");
    const early=initialMultiResponse(body as Record<string,unknown>);if(early)return Response.json(early,{headers});
    const input=validateMultiRequest(body);
    const data=await loadMultiSource(createSupabaseRead(process.env),input.simulationAt);
    return Response.json(recommendMultiple(input,data),{headers});
  }catch(error){return Response.json({schemaVersion:"queuecare.multi.v1",error:{code:error instanceof MultiInputError?"INVALID_REQUEST":"INTERNAL_ERROR",message:error instanceof MultiInputError?error.message:"Specialist comparison data is unavailable. No fixture data was substituted."}},{status:error instanceof MultiInputError?422:500,headers});}
}
