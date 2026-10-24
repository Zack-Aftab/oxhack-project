#!/usr/bin/env python3
"""Build small, reproducible API examples from the supplied synthetic dataset.

This is an offline fixture generator, not an API server or a clinical model.
The original 23 MB input stays outside the repository.
"""
import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "queuecare.v1"
SCENARIO = "demo-1"
AT = "2026-09-25T18:00:00+01:00"
CATEGORY = "fracture_sprain_or_dislocation"
NOTICE = "Synthetic demonstration. Real hospital names; invented operational data. Not clinical guidance."
# Added for UI demonstration. These values do NOT come from the input dataset
# or a routing provider, and do not describe an actual journey.
DEMO_TRAVEL = {"H001": 24, "H002": 18, "H003": 12, "H004": 20, "H005": 32}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def build(source):
    raw = source.read_bytes()
    data = json.loads(raw)
    metadata = data["dataset_metadata"]
    require(metadata.get("synthetic_data") is True, "Expected the agreed synthetic input")
    hospitals = data["hospitals"]
    visits = data["visits"]
    snapshots = data["staffing_snapshots"]
    hospital_ids = {h["hospital_id"] for h in hospitals}
    require(hospital_ids == set(DEMO_TRAVEL), "Hospital catalog changed; review the agreement")
    require(len(hospitals) == len(hospital_ids), "Duplicate hospital IDs")
    require(len(visits) == metadata["total_visit_records"], "Visit metadata count mismatch")
    require(len(snapshots) == metadata["total_staffing_snapshots"], "Snapshot metadata count mismatch")
    require(len({v["visit_id"] for v in visits}) == len(visits), "Duplicate visit IDs")
    require(len({s["snapshot_id"] for s in snapshots}) == len(snapshots), "Duplicate snapshot IDs")

    categories = {}
    buckets = defaultdict(list)
    arrivals = Counter()
    days = Counter()
    snapshot_by_hospital = defaultdict(list)
    for v in visits:
        hid = v["hospital_id"]
        require(hid in hospital_ids, "Visit references an unknown hospital")
        a = datetime.fromisoformat(v["arrival_at"])
        referral = datetime.fromisoformat(v["referral_at"])
        diagnosis = datetime.fromisoformat(v["diagnosis_at"])
        w1 = v["wait_reception_to_doctor_referral_minutes"]
        w2 = v["wait_doctor_referral_to_diagnosis_minutes"]
        total = v["estimated_total_arrival_to_diagnosis_minutes"]
        require(all(type(n) is int and n >= 0 for n in [w1, w2, total]), "Invalid visit duration")
        require(total == w1 + w2, "Wait components do not sum")
        require((referral - a).total_seconds() == 60 * w1, "Referral timestamp mismatch")
        require((diagnosis - referral).total_seconds() == 60 * w2, "Diagnosis timestamp mismatch")
        category = v["complaint_category"]
        value = {"id": category, "label": v["complaint_category_label"],
                 "demoSpecialty": v["required_specialty_for_demo_model"]}
        require(category not in categories or categories[category] == value, "Category mapping changed within input")
        categories[category] = value
        buckets[hid, a.weekday(), a.hour // 4, category].append(v)
        arrivals[hid, a.date().isoformat(), a.hour // 4] += 1
        days[hid, a.date().isoformat()] += 1
    require(all(n == 300 for n in days.values()), "Daily generation pattern changed")
    for s in snapshots:
        hid = s["hospital_id"]
        require(hid in hospital_ids, "Snapshot references an unknown hospital")
        start = datetime.fromisoformat(s["snapshot_at"])
        end = datetime.fromisoformat(s["staffing_window_end"])
        require(end - start == timedelta(hours=4), "Unexpected staffing window")
        counts = [s[k] for k in ["general_doctors_available", "beds_available",
                  "patients_waiting_for_doctor_referral", "patients_waiting_for_diagnosis",
                  "arrivals_during_next_4h"]] + list(s["specialty_doctors_available"].values())
        require(all(type(n) is int and n >= 0 for n in counts), "Invalid snapshot count")
        require(s["arrivals_during_next_4h"] == arrivals[hid, start.date().isoformat(), start.hour // 4],
                "Window arrivals disagree with visits")
        snapshot_by_hospital[hid].append(s)

    def snapshot(hid, moment):
        matches = [s for s in snapshot_by_hospital[hid]
                   if datetime.fromisoformat(s["snapshot_at"]) <= moment < datetime.fromisoformat(s["staffing_window_end"])]
        require(len(matches) == 1, "Missing or overlapping snapshot at demo time")
        return matches[0]

    def baseline(hid, moment, category):
        rows = buckets[hid, moment.weekday(), moment.hour // 4, category]
        require(bool(rows), "Missing historical comparison bucket")
        return {
            "sampleCount": len(rows),
            "meanWaitToReferralMinutes": sum(v["wait_reception_to_doctor_referral_minutes"] for v in rows) / len(rows),
            "meanReferralToDiagnosisMinutes": sum(v["wait_doctor_referral_to_diagnosis_minutes"] for v in rows) / len(rows),
            "meanArrivalToDiagnosisMinutes": sum(v["estimated_total_arrival_to_diagnosis_minutes"] for v in rows) / len(rows),
        }

    def meta(version):
        return {"schemaVersion": SCHEMA, "syntheticData": True, "notice": NOTICE,
                "scenarioId": SCENARIO, "stateVersion": version, "simulationAt": AT}

    def compare(category=CATEGORY, travel=True, overrides=None, version=0):
        overrides = overrides or {}
        moment = datetime.fromisoformat(AT)
        specialty = categories[category]["demoSpecialty"]
        result = {**meta(version), "complaintCategory": category, "requiredSpecialty": specialty,
                  "travelSource": "demo_fixture" if travel else "not_configured",
                  "estimateMethod": "demo_baseline_scaling_v1", "hospitals": []}
        for h in hospitals:
            hid = h["hospital_id"]
            minutes = DEMO_TRAVEL[hid] if travel else None
            arrival = moment + timedelta(minutes=minutes) if minutes is not None else None
            reference_at = arrival or moment
            s = snapshot(hid, reference_at)
            general = overrides.get(s["snapshot_id"], s["general_doctors_available"])
            specialty_count = general if specialty == "emergency_medicine" else s["specialty_doctors_available"].get(specialty)
            suitability = "unknown" if category == "unknown" or specialty_count is None else (
                "demo_match" if general > 0 and specialty_count > 0 else "demo_unavailable")
            b = baseline(hid, reference_at, category)
            predicted = math.ceil(b["meanWaitToReferralMinutes"] * s["general_doctors_available"] / general) if (
                arrival is not None and suitability == "demo_match" and general > 0 and s["general_doctors_available"] > 0) else None
            item = {
                "hospitalId": hid, "name": h["name"], "suitability": suitability,
                "travelMinutes": minutes, "estimatedArrivalAt": arrival.isoformat() if arrival else None,
                "predictedWaitToReferralOnArrivalMinutes": predicted,
                "totalToReferralMinutes": minutes + predicted if predicted is not None else None,
                "staffingSnapshotId": s["snapshot_id"], "historicalBaseline": b,
                "explanation": "Retrospective synthetic baseline with a demo staffing multiplier; not a clinical forecast." if predicted is not None else (
                    "Travel is not configured; arrival-time and total estimates are unavailable." if not travel else
                    "No comparable estimate is available under the demo resource rules.")}
            result["hospitals"].append(item)
        result["hospitals"].sort(key=lambda h: (h["totalToReferralMinutes"] is None,
                                               h["totalToReferralMinutes"] or 0, h["hospitalId"]))
        return result

    def dashboard(overrides=None, version=0):
        overrides = overrides or {}
        moment = datetime.fromisoformat(AT)
        result = {**meta(version), "hospitals": []}
        for h in hospitals:
            s = snapshot(h["hospital_id"], moment)
            result["hospitals"].append({
                "hospitalId": h["hospital_id"], "name": h["name"],
                "snapshotId": s["snapshot_id"], "windowStart": s["snapshot_at"], "windowEnd": s["staffing_window_end"],
                "generalDoctorsAvailable": overrides.get(s["snapshot_id"], s["general_doctors_available"]),
                "baselineGeneralDoctorsAvailable": s["general_doctors_available"],
                "specialtyDoctorsAvailable": s["specialty_doctors_available"], "bedsAvailable": s["beds_available"],
                "waitingForReferral": s["patients_waiting_for_doctor_referral"],
                "waitingForDiagnosis": s["patients_waiting_for_diagnosis"],
                "historicalArrivalsInWindow": s["arrivals_during_next_4h"],
                "baselineStaffingStatus": s["simulated_staffing_status"],
                "waitBaselineByCategory": {c: baseline(h["hospital_id"], moment, c) for c in sorted(categories)},
            })
        return result

    selected = snapshot("H001", datetime.fromisoformat(AT))
    changed_count = selected["general_doctors_available"] // 2
    overrides = {selected["snapshot_id"]: changed_count}
    request = {"scenarioId": SCENARIO, "simulationAt": AT, "complaintCategory": CATEGORY,
               "originId": "london-demo", "travelMode": "demo"}
    catalog = {"schemaVersion": SCHEMA, "syntheticData": True, "notice": NOTICE,
               "timezone": metadata["timezone"], "dateRange": metadata["date_range"],
               "hospitals": [{"hospitalId": h["hospital_id"], "name": h["name"], "address": h["address"],
                              "latitude": h["latitude"], "longitude": h["longitude"]} for h in hospitals],
               "complaintCategories": [categories[c] for c in sorted(categories)],
               "demoOrigin": {"originId": "london-demo", "label": "Illustrative London origin; journeys are invented"},
               "defaultComparison": request}
    manifest = {"sourceFile": source.name, "sourceSha256": hashlib.sha256(raw).hexdigest(),
                "sourceCounts": {"hospitals": len(hospitals), "visits": len(visits), "staffingSnapshots": len(snapshots)},
                "defaultSimulationAt": AT,
                "baselineMethod": "Mean for hospital + weekday + four-hour arrival bucket + complaint category, across the full synthetic dataset",
                "travelSource": "ADDED DEMO VALUES, NOT PRESENT IN THE SOURCE DATASET OR A ROUTING API",
                "demoTravelMinutesByHospital": DEMO_TRAVEL,
                "capacityChange": {"hospitalId": "H001", "snapshotId": selected["snapshot_id"],
                                   "fromGeneralDoctors": selected["general_doctors_available"], "toGeneralDoctors": changed_count},
                "checks": "Unique IDs, hospital references, visit durations and timestamps, 300 daily visits per hospital, four-hour windows, nonnegative counts and exact window arrivals passed"}
    outputs = {
        "manifest.json": manifest,
        "catalog.response.json": catalog,
        "compare.request.json": request,
        "compare.response.json": compare(),
        "compare.capacity-changed.response.json": compare(overrides=overrides, version=1),
        "compare.no-travel.response.json": compare(travel=False),
        "compare.unknown-category.response.json": compare(category="unknown"),
        "compare.no-general-doctors.response.json": compare(overrides={selected["snapshot_id"]: 0}, version=1),
        "dashboard.response.json": dashboard(),
        "dashboard.capacity-changed.response.json": dashboard(overrides=overrides, version=1),
        "capacity.request.json": {"simulationAt": AT, "expectedStateVersion": 0, "generalDoctorsAvailable": changed_count},
        "error.validation.response.json": {"schemaVersion": SCHEMA, "error": {"code": "INVALID_REQUEST", "message": "complaintCategory must be a catalog ID"}},
    }

    # Cross-screen acceptance checks, independent of rendering or database choice.
    before = {h["hospitalId"]: h for h in outputs["compare.response.json"]["hospitals"]}
    after = {h["hospitalId"]: h for h in outputs["compare.capacity-changed.response.json"]["hospitals"]}
    require(after["H001"]["predictedWaitToReferralOnArrivalMinutes"] >= before["H001"]["predictedWaitToReferralOnArrivalMinutes"], "Staffing scenario moves in the wrong direction")
    require(all(before[h] == after[h] for h in hospital_ids - {"H001"}), "Capacity change leaked to other hospitals")
    for filename, response in outputs.items():
        if not filename.startswith("compare.") or "hospitals" not in response:
            continue
        for h in response["hospitals"]:
            total, wait, travel = h["totalToReferralMinutes"], h["predictedWaitToReferralOnArrivalMinutes"], h["travelMinutes"]
            require(total is None if wait is None or travel is None else total == wait + travel, "Comparison total mismatch")
            require(h["historicalBaseline"]["sampleCount"] > 0, "Empty baseline")
    require(all(h["totalToReferralMinutes"] is None for h in outputs["compare.no-travel.response.json"]["hospitals"]), "Unknown travel became a zero journey")
    require(all(h["suitability"] == "unknown" for h in outputs["compare.unknown-category.response.json"]["hospitals"]), "Unknown complaint received an asserted match")
    return {name: json.dumps(value, ensure_ascii=False, indent=2) + "\n" for name, value in outputs.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Path to QueueCare Mock Dataset.json")
    parser.add_argument("--output", type=Path, default=ROOT / "fixtures" / "queuecare")
    parser.add_argument("--check", action="store_true", help="Verify committed examples without rewriting them")
    args = parser.parse_args()
    outputs = build(args.source)
    if args.check:
        for name, content in outputs.items():
            target = args.output / name
            require(target.is_file() and target.read_text() == content, "Fixture differs: " + name)
        print(f"Verified source integrity, cross-screen invariants and {len(outputs)} reproducible JSON examples.")
    else:
        args.output.mkdir(parents=True, exist_ok=True)
        for name, content in outputs.items():
            (args.output / name).write_text(content)
        print(f"Wrote {len(outputs)} small JSON examples to {args.output}")


if __name__ == "__main__":
    main()
