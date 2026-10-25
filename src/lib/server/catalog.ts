import type { CatalogResponse, ComplaintCategory, Hospital, SpecialtyId } from "../../../contracts/queuecare.ts";

// Display metadata for the agreed category IDs, not hospital capability claims.
const definitions: Record<ComplaintCategory, { label: string; demoSpecialty: SpecialtyId }> = {
  fracture_sprain_or_dislocation: { label: "Fracture, sprain or dislocation", demoSpecialty: "orthopaedics" },
  cuts_or_wounds: { label: "Cuts or wounds", demoSpecialty: "wound_care_or_plastics" },
  head_injury_or_neurological_symptoms: { label: "Head injury or neurological symptoms", demoSpecialty: "neurology_or_neurosurgery" },
  breathing_problems: { label: "Breathing problems", demoSpecialty: "respiratory_medicine" },
  chest_pain_or_heart_symptoms: { label: "Chest pain or heart symptoms", demoSpecialty: "cardiology" },
  abdominal_or_stomach_problems: { label: "Abdominal or stomach problems", demoSpecialty: "general_surgery_or_gastroenterology" },
  other_or_uncategorised: { label: "Other/uncategorised", demoSpecialty: "emergency_medicine" },
  unknown: { label: "Unknown", demoSpecialty: "emergency_medicine" },
};
export type SupabaseRead = (table: string, query: Record<string, string>) => Promise<unknown>;

function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("Invalid database object");
  return value as Record<string, unknown>;
}
function text(value: unknown): string {
  if (typeof value !== "string" || !value.trim()) throw new Error("Missing database text");
  return value;
}
function date(value: unknown): string {
  const result = text(value);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(result) || new Date(`${result}T00:00:00Z`).toISOString().slice(0, 10) !== result) throw new Error("Invalid dataset date");
  return result;
}

export async function loadCatalog(read: SupabaseRead, datasetId = "month-v5"): Promise<CatalogResponse> {
  const [rawHospitals, rawDatasets] = await Promise.all([
    read("hospitals", { select: "hospital_id,name,address,latitude,longitude", order: "hospital_id.asc" }),
    read("simulation_datasets", { select: "dataset_id,model_version,metadata", dataset_id: `eq.${datasetId}`, limit: "1" }),
  ]);
  if (!Array.isArray(rawHospitals) || !rawHospitals.length || !Array.isArray(rawDatasets) || rawDatasets.length !== 1) throw new Error("Catalog data unavailable");
  const ids = new Set<string>();
  const hospitals: Hospital[] = rawHospitals.map(value => {
    const row = object(value);
    const id = text(row.hospital_id);
    if (ids.has(id)) throw new Error("Duplicate hospital ID");
    ids.add(id);
    if (typeof row.latitude !== "number" || !Number.isFinite(row.latitude) || Math.abs(row.latitude) > 90 || typeof row.longitude !== "number" || !Number.isFinite(row.longitude) || Math.abs(row.longitude) > 180) throw new Error("Invalid hospital coordinates");
    return { hospitalId: id, name: text(row.name), address: text(row.address), latitude: row.latitude, longitude: row.longitude };
  });
  hospitals.sort((a, b) => a.hospitalId.localeCompare(b.hospitalId));
  const dataset = object(rawDatasets[0]);
  if (dataset.dataset_id !== datasetId) throw new Error("Wrong dataset");
  const metadata = object(dataset.metadata);
  if (metadata.synthetic_data !== true || metadata.timezone !== "Europe/London") throw new Error("Unexpected dataset provenance");
  // The current schema stores supported category IDs in imported dataset metadata.
  // No visits, fixtures, category probabilities or wait estimates are sent to the browser.
  const categoryIds = Object.keys(object(metadata.category_specific_flag_probabilities)).sort();
  if (!categoryIds.length) throw new Error("Missing category catalog");
  const complaintCategories = categoryIds.map(id => {
    if (!Object.hasOwn(definitions, id)) throw new Error("Unsupported database category");
    const category = id as ComplaintCategory;
    return { id: category, ...definitions[category] };
  });
  const start = date(metadata.measured_start);
  const exclusiveEnd = date(metadata.measured_end_exclusive);
  if (exclusiveEnd <= start) throw new Error("Invalid dataset period");
  const end = new Date(Date.parse(`${exclusiveEnd}T00:00:00Z`) - 86400000).toISOString().slice(0, 10);
  const simulationAt = "2026-09-25T18:00:00+01:00";
  if (simulationAt.slice(0, 10) < start || simulationAt.slice(0, 10) > end || !categoryIds.includes("fracture_sprain_or_dislocation")) throw new Error("Default comparison unavailable in dataset");
  return {
    schemaVersion: "queuecare.v1", syntheticData: true, notice: text(metadata.notice), timezone: "Europe/London",
    dateRange: { start, end, inclusive: true }, hospitals, complaintCategories,
    demoOrigin: { originId: "london-demo", label: "Illustrative London origin; journeys are invented" },
    defaultComparison: { scenarioId: "demo-1", simulationAt, complaintCategory: "fracture_sprain_or_dislocation", originId: "london-demo", travelMode: "demo" },
  };
}
