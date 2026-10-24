# Backend handoff

Prepared 24 October 2026. This report records inspected evidence and decisions; it does not define a new implementation plan.

Status labels: **running/tested** means execution was verified; **written but untested** means an artifact or snippet exists without verified execution; **planned** means discussed intent only; **unknown** means evidence is unavailable. No application endpoint is verified running/tested.

## 1. Stack and code location

**Planned — main application:** React, Next.js App Router, TypeScript, Tailwind CSS; Next.js Route Handlers; Supabase Postgres; Vercel; Node.js 24 LTS and npm. These were the selected stack in the discussion, not an inspected installation.

**Unknown — shared application:** The user says a friend has the app. Repository URL supplied: https://github.com/ajjarm/oxhack-project/pull/1. Repository contents, current branch, application scaffold, package versions, deployment and merged code could not be inspected. A branch named `feature/image-classification` was suggested in chat, but creation was not verified.

**Written but untested — inspected local artifacts:** `/workspace/scratch/b4d2fdcbf9de/image-classifier/` contains `.env`, `.gitignore`, `server.mjs`, and `public/index.html`. The backend and HTML files are both **zero bytes**. The environment file contains placeholder configuration; no credential values are included here. `.gitignore` excludes dependencies and the environment file. An `image-classifier.zip` archive was created. No `package.json`, installed dependency tree, Next.js scaffold or Git checkout was found in this scoped workspace. The workspace's Git status command reports that it is not a Git repository.

**Written but untested — chat snippets only:** A Next.js classifier route and client upload example, followed by a separate Express/Multer classifier server and drag-and-drop HTML page. These snippets were not populated into the inspected empty files. The standalone Express example is a local experiment, not evidence of a change to the selected main application stack.

## 2. Database and source data

**Unknown — live database:** No Supabase project, SQL schema, tables, primary/foreign-key constraints, RLS policies, migrations, import scripts or migration/import execution were inspected. No database connection or successful query was verified. JSON collections below are not confirmed SQL tables.

**Written but untested — dataset artifact:** The file previously referenced as `queuecare_mock_dataset(1).json` currently resolves to `queuecare_mock_dataset_month.json`, version 1. Its metadata and selected hospital, visit and staffing records were read. The complete 23 MB dataset was not exhaustively validated.

Metadata declares 21 September–18 October 2026 inclusive (28 days), 300 visits per hospital per day, 1,500 across five hospitals per day, 42,000 visits total, six staffing snapshots per hospital per day and 840 snapshots total. These counts are metadata declarations, not results of a full-file validation. Despite the filename, the range is four weeks rather than a full calendar month.

| JSON collection | Important fields and observed types | Identifier / relationship meaning |
| --- | --- | --- |
| `dataset_metadata` | title, simulation disclaimers and timezone strings; date-range object; integer counts and seed; field-description object | File-level metadata; no database key verified |
| `hospitals` | `hospital_id`, `name`, `address`, source URLs and simulation profile strings; numeric `latitude`, `longitude`, `synthetic_load_factor` | `hospital_id` is the dataset linking identifier; no SQL PK verified |
| `visits` | `visit_id`, `hospital_id`, `complaint_category`, `complaint_category_label`, `required_specialty_for_demo_model`; three integer minute fields; `arrival_at`, `referral_at`, `diagnosis_at` timestamp strings | `visit_id` is described as unique; `hospital_id` links to hospitals; no SQL PK/FK verified |
| `staffing_snapshots` | `snapshot_id`, `hospital_id`, `snapshot_at`, `staffing_window_end`; integer doctor, bed, queue and arrival counts; `specialty_doctors_available` object; status and basis strings | Snapshot identifier and hospital link exist in JSON; no SQL PK/FK verified |

| Hospital identifier | Dataset hospital name |
| --- | --- |
| `H001` | The Royal London Hospital |
| `H002` | St Mary’s Hospital |
| `H003` | University College Hospital |
| `H004` | St Thomas’ Hospital |
| `H005` | King’s College Hospital |

The names/addresses identify real sites according to the dataset. Operational data, staffing, coverage, beds, queues, demand patterns and waits are explicitly invented. Hospital operational facts were not independently verified for this handoff.

## 3. API contracts

### Main patient and hospital operations

**Planned — capabilities; unknown — contracts and implementation.** No inspected code or accessible contract establishes the following endpoints:

| Operation | Exact method/path | Authentication | Request / success / error JSON |
| --- | --- | --- | --- |
| Patient hospital comparison | Unknown; missing from inspected local work | Unknown | Not defined or inspected |
| Hospital dashboard | Unknown; missing from inspected local work | Unknown | Not defined or inspected |
| Capacity update | Unknown; missing from inspected local work | Unknown | Not defined or inspected |

Complete representative request/success/error JSON for these three operations cannot be supplied honestly: none was established in the visible discussion or inspectable code. No JSON examples here should be treated as their contracts. HTTP status codes, query parameters, pagination, validation, authorization and error envelopes are also unknown. Missing endpoints are a current integration gap, not verified 404 responses from a live server.

### Optional image classification

**Written but untested — latest standalone chat example:** `POST /classify`, multipart/form-data with one binary field named `image`. This request is **not JSON**. No caller authentication is implemented in that snippet; the Gemini API key is used by the server, not supplied by the browser. JPEG, PNG and WebP MIME values are accepted with a 3 MiB upload limit. MIME checking is not full image decoding/validation.

Representative success, HTTP 200:

```json
{"category":"cuts or wounds"}
```

Complete error bodies written in that snippet:

```json
{"error":"Upload a JPG, PNG or WebP image under 3 MB."}
```

HTTP 400 for a missing/unsupported image.

```json
{"error":"Image must be smaller than 3 MB."}
```

HTTP 400 for the Multer file-size limit.

```json
{"error":"Upload failed."}
```

HTTP 400 from the generic upload/error middleware.

```json
{"error":"Classification failed. Check your server terminal."}
```

HTTP 502 for a failed Gemini call, parsing failure or invalid category. No actual response was observed.

**Written but untested — earlier Next.js chat alternative:** `POST /api/classify`, multipart fields `image` (optional file) and `symptoms` (optional string; at least one input required; text limit 2,000 characters). No caller authentication was implemented. Success differs from the standalone example:

```json
{"suggestedCategory":"cuts_or_wounds","requiresConfirmation":true}
```

Its written HTTP 400 error bodies are:

```json
{"error":"Description is too long."}
```

```json
{"error":"Provide an image or symptom description."}
```

```json
{"error":"Use a JPG, PNG or WebP smaller than 3 MB."}
```

Its written HTTP 502 body is:

```json
{"error":"Could not suggest a category. Please choose one manually."}
```

These are alternatives in chat, not two deployed routes. The latest user intent is an **optional image input when describing symptoms is difficult**. Confirmation/change of the suggested category was discussed, but no confirmation persistence endpoint exists in inspected work.

## 4. Data meanings

**Written but untested — dataset definitions and observed samples.** Types below describe JSON, not deployed Postgres column types.

- Identifiers, categories, labels and profile/status fields are strings. No patient identity is encoded in the synthetic visit key.
- Coordinates are numeric latitude/longitude in degrees; metadata describes approximate main-site coordinates. No routing travel times are included.
- Doctor, bed, queue and arrival counts are integer counts. `specialty_doctors_available` is an object mapping specialty strings to integer counts. Beds mean open ED bed/treatment spaces, not inpatient beds.
- `patients_waiting_for_doctor_referral` counts the simulated queue before referral; `patients_waiting_for_diagnosis` counts the simulated queue after referral and before diagnosis.
- `arrivals_during_next_4h` counts simulated arrivals in the four-hour window starting at `snapshot_at`; it is not verified live forecasting output.
- `snapshot_at` and `staffing_window_end` delimit a four-hour staffing window. Interval boundary inclusion for application queries is unknown.
- Metadata specifies `Europe/London`. Inspected ISO 8601 timestamps include `+01:00` (BST), for example `2026-09-21T00:00:00+01:00`. Database storage type, UTC conversion and frontend formatting are unknown. Arrival-date coverage does not guarantee referral/diagnosis timestamps remain within the last arrival date.
- Missing numeric/string values: no agreed null/omission/sentinel policy was found. Observed zero queue counts are actual synthetic zero counts, not missing values. `unknown` is a category, not a universal null convention.

### Waiting-time definitions

| Dataset field | Type / unit | Precisely what it measures |
| --- | --- | --- |
| `wait_reception_to_doctor_referral_minutes` | Integer minutes | Reception conversation (`arrival_at`) to referral to a doctor (`referral_at`). Metadata proposes it as the general time-to-first-doctor estimate, but referral is not proof the doctor has actually seen the patient. |
| `wait_doctor_referral_to_diagnosis_minutes` | Integer minutes | Doctor referral (`referral_at`) to synthetic diagnosis (`diagnosis_at`). Separate from the first interval. |
| `estimated_total_arrival_to_diagnosis_minutes` | Integer minutes | Sum of the two simulated intervals, from reception to diagnosis. Excludes travel and does not establish time to discharge or completion of treatment. |

An inspected sample has 57 minutes to referral plus 123 minutes referral-to-diagnosis, totaling 180 minutes. No API-level aggregated wait statistic, uncertainty range, travel-inclusive total or ranking score is implemented/defined in inspected work.

### Categories and specialty mapping

**Written but untested — observed synthetic dataset mapping:**

| Dataset `complaint_category` | `required_specialty_for_demo_model` |
| --- | --- |
| `fracture_sprain_or_dislocation` | `orthopaedics` |
| `cuts_or_wounds` | `wound_care_or_plastics` |
| `head_injury_or_neurological_symptoms` | `neurology_or_neurosurgery` |
| `breathing_problems` | `respiratory_medicine` |
| `chest_pain_or_heart_symptoms` | `cardiology` |
| `abdominal_or_stomach_problems` | `general_surgery_or_gastroenterology` |
| `other_or_uncategorised` | `emergency_medicine` |
| `unknown` | `emergency_medicine` |

The inspected staffing object contains the first six specialist keys; `emergency_medicine` is not in that sampled object. A fallback from that specialty to general doctors has not been implemented or verified.

**Written but untested — incompatible classifier spellings:** The Next.js snippet uses `other_uncategorised`, whereas the dataset uses `other_or_uncategorised`. The standalone classifier returns human-readable strings for all eight categories (including `other/uncategorised`), rather than dataset identifiers. No normalization adapter exists in inspected files. Category labels do not establish diagnosis, clinical urgency or triage priority. The latest decision excluded an LLM-generated clinical-priority field.

## 5. Calculations and shared state

**Planned — patient matching:** Compare hospitals using general waiting time, travel time and complaint-related information. No inspected function defines eligibility, ranking weights, tie-breaking, specialty fallback or how category changes an estimate.

**Unknown — travel:** No provider, travel mode, origin format, route request, cache or calculation is implemented. Coordinates are dataset inputs, not travel-duration estimates.

**Written but untested — synthetic dataset values:** Waits are described as bounded approximately normal draws influenced by simulated workload/staffing; the referral-to-diagnosis interval also varies by category and mock specialty availability. This describes generation of invented demo records, not a validated predictor. The generator and its numeric parameters were not inspected. The total is a stored sum; no current API calculation was executed.

**Unknown — live wait estimation:** Aggregation window, mean/median/percentile choice, handling sparse samples, selected simulation time and recalculation after capacity changes are undefined in inspectable work. Historical synthetic records are not evidence of current hospital waits.

**Planned — capacity scenario controls:** Hospital-side staffing/capacity adjustments and seeing their effect on patient waits were discussed. No mutation handler or recomputation formula was inspected. Increasing a doctor count currently has no verified effect on any wait field.

**Unknown — shared scenario state:** No scenario table, scenario ID, server store, persistence mechanism or ownership model exists in inspected work. No polling, Supabase Realtime subscription, cache invalidation or other synchronization connects the two screens. The standalone HTML snippet holds only temporary upload UI state in browser memory; Multer holds an upload in server memory for the request. Neither provides shared hospital capacity state. Supabase was selected as the intended database, but that selection alone does not synchronize screens.

## 6. Running and connecting

**Unknown — runtime state:** The user reported an Ubuntu package-download failure and was advised to refresh apt indexes. No successful Node/npm version check, dependency installation, server startup, browser request, Gemini response or deployment was observed.

**Written but untested — standalone commands supplied in chat:**

```bash
cd image-classifier
npm init -y
npm install express multer @google/genai dotenv
node server.mjs
```

These are historical setup/run instructions, not commands executed by this handoff. They cannot currently serve the feature because the inspected server and HTML files are empty. Re-running `npm init` is not an instruction to alter the friend's existing app.

**Written but untested — main-app command suggestions:** `npm install` and `npm run dev` were suggested, but the repository's scripts and package manager configuration could not be checked. No migration/import command is established.

**Written but untested — environment-variable names only:** `GEMINI_API_KEY`, `GEMINI_MODEL`. No inspected Supabase, authentication or routing configuration establishes additional required names. No environment values or credentials are included in this report.

**Written but untested — URLs and browser configuration:** The standalone snippet binds `127.0.0.1:3000`, serves `public`, and expects a browser at `http://localhost:3000` using relative `fetch('/classify')`. Same-origin operation requires no separate CORS configuration; the snippet installs no cross-origin CORS middleware. Opening the HTML as a `file://` document is not the supplied setup. The Next.js example uses relative `fetch('/api/classify')` and a proposed local `/image-test` page. These are intended local addresses, not verified running backend URLs. Cross-origin frontend integration and a deployed backend URL are unknown.

## 7. Integration readiness and blockers

**Running/tested:** No backend or database feature qualifies on available evidence. Local artifact presence and empty file sizes were inspected; this is not an application test.

**Written but untested:** The synthetic dataset is available for sample inputs and the chat contains classifier examples. The inspected local application files expose no executable integration surface.

**Unknown — what the frontend can connect to now:** No verified live endpoint. The friend's application may contain additional work, but its contents were inaccessible. Do not point the frontend at a chat example as though a server already implements it.

**Planned — sample-data dependency:** Patient comparison and the dashboard were intended to use the synthetic visits/staffing/hospitals. No import or HTTP data-serving layer was verified. Capacity controls also lack a defined shared scenario and derived values.

The few unresolved decisions/evidence gaps blocking integration are:

1. Actual application branch, existing scaffold, implemented endpoints and reachable backend URL.
2. Comparison/dashboard/capacity request-response contracts and authentication/authorization requirements.
3. Deployed database schema/import status, shared capacity-scenario storage and screen synchronization behavior.
4. Wait statistic and time window, referral-versus-seen-by-doctor meaning, ranking/travel rules and simulation clock.
5. Which classifier variant is being integrated and how its category strings map to dataset identifiers.

## 8. Comparison with PR #1

**Unknown — proposal inaccessible:** https://github.com/ajjarm/oxhack-project/pull/1 could not be read. GitHub connector attempts to fetch the PR and patch, and list installed accounts, returned `This app tool requires a non-empty string link_id argument`. The public-page fallback also failed. No repository branch, PR status, proposed API contract or patch was retrieved. Consequently no differences against that proposal can be verified or listed. No code was changed to match it, and this report does not treat it as an implemented contract.

## Evidence boundaries

Inspected: scoped local file inventory, backend/HTML byte counts, absence of a local Git repository, current dataset metadata and selected records. Discussed but not executed: both classifier implementations and setup commands. Not inspected: the friend's application, PR proposal, live Supabase or Vercel state. Dataset metadata was read as artifact documentation, not independently established hospital facts. No implementation code was changed while producing this report.
