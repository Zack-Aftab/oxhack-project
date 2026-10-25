import assert from "node:assert/strict";
import { test } from "node:test";
import { addMinutes, formatClock, formatMean, formatMinutes } from "../format.ts";

test("clock renders Europe/London 24h time from offset-aware ISO", () => {
  assert.equal(formatClock("2026-09-25T18:12:00+01:00"), "18:12");
  assert.equal(formatClock("2026-09-25T17:12:00Z"), "18:12");
  assert.equal(formatClock(null), "—");
  assert.equal(formatClock("not a date"), "—");
});

test("minutes and means never render unknown values as zero", () => {
  assert.equal(formatMinutes(null), "—");
  assert.equal(formatMinutes(0), "0 min");
  assert.equal(formatMinutes(55), "55 min");
  assert.equal(formatMinutes(125), "2 h 05");
  assert.equal(formatMean(null), "—");
  assert.equal(formatMean(73.3243), "73");
});

test("addMinutes keeps the instant and adds whole minutes", () => {
  assert.equal(formatClock(addMinutes("2026-09-25T18:12:00+01:00", 74)), "19:26");
});
