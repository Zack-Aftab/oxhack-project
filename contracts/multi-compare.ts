import type { ComplaintCategory, SpecialtyId } from "./queuecare";

/** New, explicitly versioned contract; the existing single-category API is unchanged. */
export interface MultiCompareRequest {
  complaintCategories: ComplaintCategory[];
  urgencyRating: number | null; // finite float 1–10; null only while manual categorisation is pending
  likelyBedOccupancy: boolean;
  isEmergency: boolean;
  simulationAt: string;
  originId: "london-demo";
  travelMode: "demo";
}
export interface MultiHospitalRecommendation {
  hospitalId: string;
  name: string;
  requiredSpecialties: SpecialtyId[];
  doctorsOnDuty: Partial<Record<SpecialtyId, number>>;
  travelMinutes: number;
  estimatedWaitMinutes: number;
  totalMinutes: number;
  estimateSource: "simulation_urgency_band" | "simulation_hospital_fallback";
  sampleCount: number;
}
export interface MultiCompareResponse {
  schemaVersion: "queuecare.multi.v1";
  syntheticData: true;
  notice: string;
  action: "recommendations" | "self_categorise" | "call_999";
  message: string;
  effectiveUrgencyRating: number | null;
  complaintCategories: ComplaintCategory[];
  hospitals: MultiHospitalRecommendation[];
  excludedHospitals: { hospitalId: string; missingSpecialties: SpecialtyId[] }[];
}
