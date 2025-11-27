# Signal Profile Glaze CLI

Use `wb signal-profile glaze` to run the positivity-tuned bio generator once snapshots are available, and `wb signal-profile freshness` to mark highlights stale whenever new Signal activity arrives.

## Usage
```
wb signal-profile glaze --all --model openai/gpt-5-mini --glaze-dir storage/signal_profiles/glazed
```

Key flags (glaze):
- `--user <id>` / `--all`: choose targets (same as snapshot mode).
- `--group-slug <slug>`: limit to a single Signal group.
- `--model <alias>`: override the LLM alias passed to Dedalus.
- `--max-users N`: stop after N users (throttle spend).
- `--dry-run`: preview guardrail outcomes without writing bios.
- `--resume-file storage/signal_profile_glaze.resume.json`: skip user IDs already glazed and persist newly completed IDs for later resumes.

Freshness scan example:
```
wb signal-profile freshness --all
```
This command rebuilds each user’s snapshot, compares hashes/last seen timestamps, and (unless `--dry-run` is set) marks stale highlights in the database so the next glaze run refreshes them automatically.

Outputs land in `storage/signal_profiles/glazed/<user>-<group>.glaze.json` with the structured payload + guardrail metadata. Each run also appends a JSON line to `storage/signal_profile_glaze.log` capturing attempt counts, guardrail fallback totals, runtime, and dry-run status.

## Metrics
If `STATSD_HOST` is set, the CLI emits:
- `signal_glaze.snapshots_generated` (snapshot mode)
- `signal_glaze.bios_generated` (glaze mode)
- `signal_glaze.guardrail_fallbacks` (count of LLM runs replaced by fallback copy)
- `signal_glaze.highlights_stale` (freshness scan marks)

Use these counters to alert on high fallback rates or unexpected volume.

## Failure Handling & Runbook
- Guardrail violations or LLM errors automatically fall back to deterministic bios while recording the issue list inside each JSON output.
- Resume files make reruns idempotent; delete the resume file to force a full regeneration.
- Structured logs under `storage/` provide quick forensics (who ran, how long, dry-run vs write).
- If a highlight is missing or marked stale, the member/admin UIs fall back to the standard profile layout until the glaze job runs again.
- To reseed a highlight manually: `wb signal-profile glaze --user <id>` (or submit a manual override via `/admin/profiles/<id>`), then verify via `wb signal-profile freshness --user <id>`.
