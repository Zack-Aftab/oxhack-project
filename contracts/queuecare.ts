/** QueueCare API v1. Dataset-backed examples: fixtures/queuecare/.
 * These types are the shared wire format, not the database schema.
 * Backend handlers must also validate incoming JSON at runtime.
 */
export type ComplaintCategory =
  | "fracture_sprain_or_dislocation"
  | "cuts_or_wounds"
  | "head_injury_or_neurological_symptoms"
  | "breathing_problems"
  | "chest_pain_or_heart_symptoms"
  | "abdominal_or_stomach_problems"
  | "other_or_uncategorised"
  | "unknown";

export type SpecialtyId =
  | "orthopaedics"
  | "wound_care_or_plastics"
  | "neurology_or_neurosurgery"
  | "respiratory_medicine"
  | "cardiology"
  | "general_surgery_or_gastroenterology"
  | "emergency_medicine";

export type SpecialistId = Exclude<SpecialtyId, "emergency_medicine">;

export interface Hospital {
  hospitalId: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
}

export interface CompareRequest {
  scenarioId: string;
  simulationAt: string;
  complaintCategory: ComplaintCategory;
  originId: "london-demo";
  travelMode: "demo" | "unavailable";
}

export interface CatalogResponse {
  schemaVersion: "queuecare.v1";
  syntheticData: true;
  notice: string;
  timezone: "Europe/London";
  dateRange: { start: string; end: string; inclusive: true };
  hospitals: Hospital[];
  complaintCategories: {
    id: ComplaintCategory;
    label: string;
    demoSpecialty: SpecialtyId;
  }[];
  demoOrigin: { originId: "london-demo"; label: string };
  defaultComparison: CompareRequest;
}

export interface ScenarioMeta {
  schemaVersion: "queuecare.v1";
  syntheticData: true;
  notice: string;
  scenarioId: string;
  stateVersion: number;
  simulationAt: string;
}

export interface HistoricalBaseline {
  sampleCount: number;
  meanWaitToReferralMinutes: number | null;
  meanReferralToDiagnosisMinutes: number | null;
  meanArrivalToDiagnosisMinutes: number | null;
}

export interface HospitalComparison {
  hospitalId: string;
  name: string;
  suitability: "demo_match" | "demo_unavailable" | "unknown";
  travelMinutes: number | null;
  estimatedArrivalAt: string | null;
  predictedWaitToReferralOnArrivalMinutes: number | null;
  totalToReferralMinutes: number | null;
  staffingSnapshotId: string;
  historicalBaseline: HistoricalBaseline;
  explanation: string;
}

export interface CompareResponse extends ScenarioMeta {
  complaintCategory: ComplaintCategory;
  requiredSpecialty: SpecialtyId;
  travelSource: "demo_fixture" | "not_configured";
  estimateMethod: "demo_baseline_scaling_v1";
  hospitals: HospitalComparison[];
}

export interface HospitalDashboard {
  hospitalId: string;
  name: string;
  snapshotId: string;
  windowStart: string;
  windowEnd: string;
  generalDoctorsAvailable: number;
  baselineGeneralDoctorsAvailable: number;
  specialtyDoctorsAvailable: Record<SpecialistId, number>;
  bedsAvailable: number;
  waitingForReferral: number;
  waitingForDiagnosis: number;
  historicalArrivalsInWindow: number;
  baselineStaffingStatus:
    | "understaffed"
    | "adequately_staffed_in_simulation"
    | "overstaffed_relative_to_simulated_demand";
  waitBaselineByCategory: Record<ComplaintCategory, HistoricalBaseline>;
}

export interface DashboardResponse extends ScenarioMeta {
  hospitals: HospitalDashboard[];
}

/** Absolute general-doctor count for the hospital's selected four-hour window. */
export interface CapacityRequest {
  simulationAt: string;
  expectedStateVersion: number;
  generalDoctorsAvailable: number;
}

/** Successful capacity update returns the full DashboardResponse. */
export interface ErrorResponse {
  schemaVersion: "queuecare.v1";
  error: {
    code:
      | "INVALID_REQUEST"
      | "UNKNOWN_RESOURCE"
      | "SIMULATION_TIME_UNAVAILABLE"
      | "STATE_CONFLICT"
      | "INTERNAL_ERROR";
    message: string;
    currentStateVersion?: number;
  };
}
