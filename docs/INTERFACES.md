# Integration agreements

Define just enough for independently built components to connect. Do this before both sides implement an interface.

For each boundary record:

- Purpose and owning task/person.
- Input: field names, types, required values and validation.
- Output: shape, empty state and failure cases.
- Authentication, if applicable.
- One concrete request/input and response/output example.
- Mock/fixture behavior while the real dependency is being built.
- Source file for the executable schema, once available.

Announce a breaking change to the affected owner before implementing it. Prefer additive compatible changes where practical. Worktrees isolate files; they do not resolve incompatible assumptions.

The initial database contract is defined by `supabase/migrations/202610240001_queuecare.sql` and explained in [DATABASE.md](DATABASE.md). Historical imports use `scripts/seed-database.mjs`; server-only Supabase access is required. No application HTTP endpoints are implemented yet.

The selected database schema is now defined by `supabase/migrations/202610240003_monthly_simulation.sql`; the selected model is documented in [simulation/README.md](../simulation/README.md). It records first general-doctor contact, not the earlier referral event. The existing shared wire contract from [PR #1](https://github.com/ajjarm/oxhack-project/pull/1) is not changed here. Backend integration must coordinate the model/version and meaning with that contract before serving these data; removed diagnosis fields must not be fabricated for old responses. Scenario history is archived rather than silently mapped to a new API state model.
