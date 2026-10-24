# QueueCare dataset: short review

Reviewed `QueueCare Mock Dataset.json` on 24 October 2026. Source checksum and counts are recorded in the [fixture manifest](../fixtures/queuecare/manifest.json).

**Verdict:** consistent synthetic seed data for a hackathon. It is not yet the patient-comparison API, a routing feed or a validated queue model.

## Checks that passed

- Valid JSON: 5 hospitals, 42,000 visits and 840 staffing snapshots.
- Hospital, visit and snapshot IDs are unique; every visit/snapshot hospital reference resolves.
- Every visit's two wait intervals sum to its stored total. Referral and diagnosis timestamps match their respective durations.
- All checked durations and operational counts are nonnegative integers.
- Each staffing window is four hours. Its arrival count matches the generated visits in that window.
- Exactly 300 generated visits exist per hospital per day, as the metadata states.

## The catches to preserve in the app

1. **All operations are invented.** Hospital names are real, but queues, staffing, waits and apparent demand patterns are synthetic. The linked hospital pages are not evidence for those invented numbers. No external verification of addresses/coordinates was performed in this review.
2. **There are two different wait stages.** Reception-to-referral is separate from referral-to-diagnosis. The stored total excludes travel. There is no separate doctor-seen, discharge or completed-treatment timestamp.
3. **No travel durations or clinical-priority labels exist.** Coordinates alone do not supply journey times; complaint categories do not establish urgency. The fixture pack adds explicitly invented demo travel values separately.
4. **Historical time matters.** The file covers 21 September–18 October 2026, with four-hour snapshots. Its next-four-hour arrivals equal generated history, not a forecast available in real time.
5. **Daily totals are fixed.** This data cannot establish a real increase in total daily hospital demand. Within-day patterns and category mixes can illustrate the generated scenario only.
6. **`emergency_medicine` has no specialist-map entry.** `other_or_uncategorised` and `unknown` visits use that bucket; the contract maps it to general doctors. The unknown complaint remains unknown for patient comparisons.
7. **Staffing labels are baseline labels.** The source's `understaffed`/other statuses do not measure real staffing quality, and do not automatically recompute after a control changes. Beds represent ED treatment spaces, not inpatient capacity.

The source is about 23.5 MB. Keep it on the server/import side. The [small fixtures](../fixtures/queuecare/README.md) let frontend work start without downloading all visits into the browser.

## Verification

The source and examples were checked using the dependency-free fixture generator. Reproduce the checks with:

```sh
python3 scripts/prepare_queuecare_fixtures.py "/path/to/QueueCare Mock Dataset.json" --check
```

No backend, database import, UI or real-world forecast accuracy has been tested by this review.
