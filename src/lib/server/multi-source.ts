import type { SupabaseRead } from "./catalog.ts";
import { CATEGORY_SPECIALTY, SPECIALTIES, MultiInputError, type MultiCatalogData } from "./multi-compare.ts";

function row(value: unknown):Record<string,unknown>{if(!value||typeof value!=="object"||Array.isArray(value))throw new Error("Invalid specialist source");return value as Record<string,unknown>;}
export async function loadMultiSource(read: SupabaseRead, simulationAt: string):Promise<MultiCatalogData>{
  const min=Date.parse(simulationAt);const max=min+32*60000;
  const [rawHospitals,rawSupport,rawStaff,rawDataset,rawCategories]=await Promise.all([
    read("hospitals",{select:"hospital_id,name",order:"hospital_id.asc"}),
    read("hospital_specialties",{select:"hospital_id,specialty_id,supported"}),
    read("specialist_staffing",{select:"hospital_id,specialty_id,shift_start,shift_end,doctors_on_duty",shift_start:`lte.${new Date(max).toISOString()}`,shift_end:`gt.${new Date(min).toISOString()}`,limit:"100"}),
    read("simulation_datasets",{select:"metadata",dataset_id:"eq.specialist-v7",limit:"1"}),
    read("category_specialties",{select:"category_id,specialty_id,requires_manual_selection"}),
  ]);
  if(!Array.isArray(rawHospitals)||!Array.isArray(rawSupport)||!Array.isArray(rawStaff)||!Array.isArray(rawDataset)||rawDataset.length!==1)throw new Error("Specialist simulation not configured");
  if(!Array.isArray(rawCategories))throw new Error("Category mapping unavailable");
  const categorySpecialties=Object.fromEntries(rawCategories.map(row).map(r=>{
    if(typeof r.category_id!=="string"||!Object.hasOwn(CATEGORY_SPECIALTY,r.category_id)||typeof r.specialty_id!=="string"||!SPECIALTIES.includes(r.specialty_id as typeof SPECIALTIES[number])||r.requires_manual_selection!==(r.category_id==="unknown"))throw new Error("Invalid category-specialist mapping");
    return [r.category_id,r.specialty_id];
  }));
  if(Object.keys(categorySpecialties).length!==Object.keys(CATEGORY_SPECIALTY).length)throw new Error("Incomplete category-specialist mapping");
  const meta=row(row(rawDataset[0]).metadata);const estimates=row(meta.comparison_estimates);
  if(meta.synthetic_data!==true||typeof meta.measured_start!=="string"||typeof meta.measured_end_exclusive!=="string"||typeof meta.notice!=="string")throw new Error("Bad specialist metadata");
  if(min<Date.parse(`${meta.measured_start}T00:00:00+01:00`)||max>=Date.parse(`${meta.measured_end_exclusive}T00:00:00+01:00`))throw new MultiInputError("Arrival outside simulation coverage");
  const travel:Record<string,number>={H001:24,H002:18,H003:12,H004:20,H005:32};
  return {categorySpecialties:categorySpecialties as MultiCatalogData["categorySpecialties"],notice:meta.notice,measuredStart:`${meta.measured_start}T00:00:00+01:00`,measuredEndExclusive:`${meta.measured_end_exclusive}T00:00:00+01:00`,hospitals:rawHospitals.map(value=>{
    const h=row(value);if(typeof h.hospital_id!=="string"||typeof h.name!=="string")throw new Error("Bad hospital");
    const id=h.hospital_id;const arrival=min+(travel[id]??NaN)*60000;
    const support=Object.fromEntries(rawSupport.map(row).filter(r=>r.hospital_id===id).map(r=>[String(r.specialty_id),r.supported]));
    const staff=rawStaff.map(row).filter(r=>r.hospital_id===id&&Date.parse(String(r.shift_start))<=arrival&&Date.parse(String(r.shift_end))>arrival);
    if(new Set(staff.map(r=>r.specialty_id)).size!==staff.length)throw new Error("Overlapping specialist shifts");
    const onDuty=Object.fromEntries(staff.map(r=>[String(r.specialty_id),r.doctors_on_duty]));
    const estimated=row(estimates[id]);
    return {hospitalId:id,name:h.name,supported:support as Record<string,boolean>,onDuty:onDuty as Record<string,number>,estimates:row(estimated.bands) as unknown as MultiCatalogData['hospitals'][number]['estimates'],pooledEstimate:row(estimated.pooled) as unknown as {mean:number;count:number}};
  })};
}
