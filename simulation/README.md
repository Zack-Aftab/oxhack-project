# Specialist simulation

Current model: `specialists.py`, version specialist_urgency_v7. Read [the actual results and limitations](results/specialist-v7/REPORT.md). These are synthetic capability profiles and case histories, not real hospital service claims.

Reproduce from repository root using Python 3.11+ (standard library only):

```sh
python3 simulation/specialists.py simulation/input.json /tmp/specialist-results
python3 simulation/export_specialists.py /tmp/specialist-results
python3 -m unittest discover -s simulation/tests -v
```

Defaults use three warmup days, 30 measured days and five repetitions of the same patient cohort. `--help` lists optional settings. Current results retain five raw waits per completed patient and ceil their mean to an integer. Emergency exits have no hospital or wait. The archive contains a rejected strict-priority diagnostic, not the selected model.

The additive Supabase migration is `supabase/migrations/202610250002_specialist_catalog.sql`. The checked, rerunnable seed is `results/specialist-v7/seed.sql`. Apply migration before seed; these are prepared artifacts, not an assertion of live deployment. The seed includes capacity/staffing and summary metadata; full visits remain in `dataset.json.gz` for a separate optional import. Existing active monthly data is preserved.
