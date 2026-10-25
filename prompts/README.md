# Gemini demonstration intake

Use `gemini-intake.txt` as the system instruction and send patient text/image and their pain score as separate user data. The previous purpose prohibited urgency assessment; this version explicitly permits an **unvalidated demo estimate** while retaining broad categories and avoiding diagnosis/treatment claims.

`gemini-intake.schema.json` defines the JSON response contract. Configure JSON structured output with the subset supported by your Gemini model/SDK, then run `validateIntake(result, suppliedPainScore)` on the server; provider schema enforcement does not replace the cross-field checks. Pass null when no pain score was provided. These checks verify format and consistency, not clinical accuracy. Never log real symptom text/images in the demo by default.

The response adds `urgency_rating` (1-10, 10 most concern), `is_emergency`, a pain-score echo, explanation and clarification state. Insufficient information returns null rather than a fabricated urgency score or a reassuring false. Categories stay an array of the original IDs; `unknown` is exclusive. Patients confirm categories, but an emergency message must not wait for category confirmation.

After validation, `intakeAction` selects:

| Action | UI behaviour |
|---|---|
| `show_999` | Stop hospital ranking/navigation and show the app-owned message: **“Possible medical emergency. Call 999 now. Do not wait for hospital comparisons in this app.”** Keep the message visible; do not close the browser or hide it behind a form. |
| `ask_follow_up` | Show one clarification question; do not display a fabricated urgency result. |
| `confirm_categories` | Ask the patient to confirm/change categories. `is_emergency=false` means no warning signs identified from the input, not medical clearance. |

Keep access to emergency-help information available independently of the model response. Handle a Gemini timeout, malformed JSON or rejected response as an unavailable assessment, never as low urgency or `is_emergency=false`. A prompt alone cannot guarantee emergency detection. No Gemini API call, real clinical validation or app UI integration is implemented here.

Pain is self-reported input, not a proxy for urgency. Low pain must not rule out emergency warning signs. The category IDs and a normal-looking image cannot establish safety. Gemini's urgency score is separate from the simulation's `likely_bed_occupancy` flag and does not automatically change the stored simulated wait.

## Database

The additive migration `supabase/migrations/202610250001_gemini_intake.sql` adds nullable pain, urgency, emergency and provenance fields to `public.visits`. Existing 68,705 simulated visits remain unassessed; no scores are manufactured. The migration has not been applied to the live project. Run it once in Supabase SQL Editor to apply it; do not rerun the earlier replacement migration.

Trusted server code should set `urgency_assessment_source='gemini_demo'`, the actual model ID and assessment timestamp. Copy `reason` into `urgency_reason`. Do not describe model-generated values as clinician assessments. Keep the Supabase secret on the server.

The existing shared catalog/compare/dashboard wire shapes are unchanged. This is a separate model-response contract, not an implemented public endpoint. Multiple suggested categories need confirmation and an agreed adapter to the existing single complaint-category field; do not silently change that database/API contract.

## Check

```sh
node --test prompts/validate-intake.test.mjs
```

Tests cover output validation, missing information, independent pain/urgency and emergency UI actions using fabricated model outputs. They do not test Gemini's medical performance.
