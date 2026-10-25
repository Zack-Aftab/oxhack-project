import assert from "node:assert/strict";
import { test } from "node:test";
import type { CompareResponse, HospitalComparison } from "../../../contracts/queuecare.ts";
import { comparisonRows, scaleMinutes, unavailableReason } from "../comparison-view.ts";

const base: HospitalComparison = {
  hospitalId: "H001",
  name: "A",
  suitability: "demo_match",
  travelMinutes: 10,
  estimatedArrivalAt: "2026-09-25T18:10:00+01:00",
  predictedWaitToReferralOnArrivalMinutes: 50,
  totalToReferralMinutes: 60,
  staffingSnapshotId: "H001-D05-B05",
  historicalBaseline: { sampleCount: 1, meanWaitToReferralMinutes: 55, meanReferralToDiagnosisMinutes: 70, meanArrivalToDiagnosisMinutes: 125 },
  explanation: "ok",
};

function response(hospitals: HospitalComparison[]): CompareResponse {
  return {
    schemaVersion: "queuecare.v1",
    syntheticData: true,
    notice: "n",
    scenarioId: "demo-1",
    stateVersion: 0,
    simulationAt: "2026-09-25T18:00:00+01:00",
    complaintCategory: "fracture_sprain_or_dislocation",
    requiredSpecialty: "orthopaedics",
    travelSource: "demo_fixture",
    estimateMethod: "demo_baseline_scaling_v1",
    hospitals,
  };
}

test("keeps the server order and numbers only rankable rows", () => {
  const rows = comparisonRows(
    response([
      { ...base, hospitalId: "H003", totalToReferralMinutes: 86 },
      { ...base, hospitalId: "H001", totalToReferralMinutes: 121 },
      { ...base, hospitalId: "H002", suitability: "demo_unavailable", predictedWaitToReferralOnArrivalMinutes: null, totalToReferralMinutes: null },
    ]),
  );
  assert.deepEqual(
    rows.map((r) => [r.row.hospitalId, r.rank, r.ranked]),
    [
      ["H003", 1, true],
      ["H001", 2, true],
      ["H002", null, false],
    ],
  );
});

test("never ranks a row whose total or travel is unknown, even when it matches", () => {
  const rows = comparisonRows(
    response([
      { ...base, travelMinutes: null, estimatedArrivalAt: null, predictedWaitToReferralOnArrivalMinutes: null, totalToReferralMinutes: null },
      { ...base, hospitalId: "H009", suitability: "unknown", predictedWaitToReferralOnArrivalMinutes: null, totalToReferralMinutes: null },
    ]),
  );
  assert.equal(rows.filter((r) => r.ranked).length, 0);
  assert.equal(scaleMinutes(rows), 0);
});

test("shared bar scale is the largest ranked total", () => {
  const rows = comparisonRows(response([{ ...base, totalToReferralMinutes: 60 }, { ...base, hospitalId: "H002", totalToReferralMinutes: 121 }]));
  assert.equal(scaleMinutes(rows), 121);
});

test("unavailable reason prefers the server explanation and names missing travel", () => {
  assert.equal(unavailableReason({ ...base, suitability: "demo_unavailable", explanation: "Zero doctors" }), "Zero doctors");
  assert.equal(unavailableReason({ ...base, travelMinutes: null, explanation: "" }), "Travel is not configured");
});
