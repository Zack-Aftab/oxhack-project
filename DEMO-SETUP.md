# Run your edited intake demo

This keeps your Express `server.mjs` and `public/index.html` workflow. It is a standalone prototype, not yet a Next.js Route Handler or Vercel deployment.

1. Use Node.js 24 LTS. From the project folder, run `npm ci` (dependencies are pinned in `package-lock.json`).
2. Keep your existing `.env` if you have one; add missing settings rather than overwriting it. If none exists, copy `.env.example` to `.env`. Set `GEMINI_API_KEY` privately. Never send it in chat or commit it.
3. Set `GEMINI_MODEL` to an API model ID enabled for your key. The example preserves your existing `gemini-3.5-flash-lite` choice; availability has not been verified here. Change it if your Gemini account rejects it.
4. Run `npm start`, then open `http://localhost:3000` in your own browser. `npm run dev` restarts the server on changes. `PORT` can select another port.

In this cloud workspace, Gemini also needs the API destination allowed by environment networking and a securely configured key; `NODE_USE_ENV_PROXY=1 npm start` enables Node's environment proxy support. Local machines without a proxy normally just use `npm start`.

## Files to keep together

```text
server.mjs
category-rules.txt              # Active system instruction used by this server
package.json
package-lock.json
.env                           # Create locally; never commit
public/
  index.html
prompts/
  gemini-intake.schema.json     # Model response JSON schema
  validate-intake.mjs           # Server output validation and action selection
```

The active `category-rules.txt` is the revised prompt from the previous change, copied to the filename your server already used. `prompts/gemini-intake.txt` remains the shared reference in the repository. Keep the two aligned if you edit the prompt later.

No extra frontend build or database is needed to run this form. The revised page adds an unreported-or-1–10 pain selector, AI urgency display, follow-up question, and a persistent call-999 panel. It preserves image preview, drag/drop and editable category tags. Changing symptoms, pain or images invalidates old results. An emergency result disables analysis/category confirmation for that example; the explicit new-example button clears the scenario.

Pain is sent as `pain_score`; Gemini returns `urgency_rating` and `is_emergency` independently. The `/classify` response retains `suggestedCategories` and `requiresConfirmation` and adds `painScore`, `urgencyRating`, `isEmergency`, `needsMoreInformation`, `followUpQuestion`, `reason`, `action` and the app-owned `emergencyMessage`. It does not change the shared `/api/compare` contract.

Insufficient information returns a clarification state, not a fabricated score. Timeouts, quota limits and invalid responses leave urgency/emergency unassessed. The page never turns an API failure into `isEmergency=false`. It renders model text with `textContent`, not HTML. An emergency warning remains visible until the user explicitly starts a new fictional example; it does not close the browser.

This demo does not save to Supabase. The earlier additive intake-column migration is separate and has not been applied by this change. Category confirmation remains local to the page, as in your original HTML.

## Checks and limits

`npm test` runs local validation, real-HTTP server tests and DOM behaviour tests, plus existing database/import checks in the repository. The small downloadable demo bundle includes only the intake tests. Gemini responses are mocked for these checks: they test request handling and UI behaviour, not the medical accuracy of the model. There is no Gemini API key in this workspace, so a real model request was not tested.

A prompt cannot guarantee emergency recognition. Use fictional cases; this is not a validated clinical triage system. The emergency-help link remains available independently of model output.
