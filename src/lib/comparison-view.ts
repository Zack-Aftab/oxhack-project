import type { CompareResponse, HospitalComparison } from "@contracts/queuecare";

export interface ComparisonRow {
  row: HospitalComparison;
  /** Position among rankable rows in the server's order; null when the server could not rank it. */
  rank: number | null;
  ranked: boolean;
}

/**
 * The server already orders rows (ranked rows by total, then unrankable rows by ID).
 * This only annotates that order; it never re-sorts or computes a score.
 */
export function comparisonRows(response: CompareResponse): ComparisonRow[] {
  let rank = 0;
  return response.hospitals.map((row) => {
    const ranked =
      row.suitability === "demo_match" &&
      row.totalToReferralMinutes !== null &&
      row.travelMinutes !== null &&
      row.predictedWaitToReferralOnArrivalMinutes !== null;
    return { row, ranked, rank: ranked ? ++rank : null };
  });
}

/** Shared bar scale: the largest ranked total on the screen. */
export function scaleMinutes(rows: ComparisonRow[]): number {
  return rows.reduce((max, r) => (r.ranked ? Math.max(max, r.row.totalToReferralMinutes ?? 0) : max), 0);
}

export function unavailableReason(row: HospitalComparison): string {
  if (row.suitability === "demo_unavailable") return row.explanation || "Can't treat this under the demo resource rules";
  if (row.suitability === "unknown") return row.explanation || "No comparable estimate";
  if (row.travelMinutes === null) return row.explanation || "Travel is not configured";
  return row.explanation || "No estimate available";
}

export const SUITABILITY_LABEL: Record<HospitalComparison["suitability"], string> = {
  demo_match: "Simulated resource match",
  demo_unavailable: "Unavailable in this scenario",
  unknown: "Match unknown",
};
