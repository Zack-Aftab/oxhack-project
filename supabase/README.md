# Existing database: read-only catalog connection

Do not rerun these migrations against the populated project. `001` created the original demo schema and `003` archived it and created the current monthly schema. Both were manually applied previously; importing the monthly dataset was separately verified. The current catalog route does not execute SQL, seed or reset any table.

The selected dataset and reproducible importer are preserved on Zack's earlier database branch:
https://github.com/Zack-Aftab/oxhack-project/tree/codex/database-setup/simulation

Use `hospitals` plus `simulation_datasets` for the catalog. The category IDs are keys in the imported metadata's `category_specific_flag_probabilities`; the probability values are not returned. UI labels and demo-specialty labels are canonical application display metadata, not evidence of hospital capabilities. No category table or distinct-visits scan is needed for this first read.

Actual schema, differences from the old fixtures and tested commands are recorded in `docs/build/BACKEND-CONNECTION.md`. No secret or real `.env` file is included.

## Latest prepared update

See [FITTED-V11.md](FITTED-V11.md) for the complete fitted-data replacement. It was applied and independently verified live on25 October2026; see `verification/fitted-v11-live.json`. Use `downloads/APPLY_FITTED_V11.sql` rather than rerunning older migrations. The private backup and active-data switch are included.
