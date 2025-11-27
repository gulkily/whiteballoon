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

### Frontend engagement events
Member profile pages send lightweight analytics via `POST /api/metrics` with payloads like:

```
{
  "category": "profile_glaze",
  "event": "snapshot_link",
  "subject_id": 42,
  "metadata": {"reference": "https://partiful.com/...", "manual_override": false}
}
```

The endpoint simply logs the event/category, viewer ID, subject ID, and metadata (stringified) so Ops can correlate proof-click activity without storing PII.

## CLI Quick Reference
- Build or refresh Signal snapshots:
  ```
  ./wb signal-profile snapshot --all
  ```

- Generate positivity-tuned bios from existing snapshots:
  ```
  ./wb signal-profile glaze --all --model openai/gpt-5-mini --glaze-dir storage/signal_profiles/glazed
  ```

- Re-evaluate freshness after new Signal imports:
  ```
  ./wb signal-profile freshness --all
  ```

> Note: `./wb comment-llm --snapshot-label ...` is part of the comment insights labeling workflow. It does **not** create Signal profile bios. Always run the three `signal-profile` subcommands above when you need member profiles to update.

### One-touch pipeline
Use the orchestration command to run comment analyses and glazing together:

```
./wb profile-glaze --username alice --comment-model openai/gpt-4o-mini --glaze-model openai/gpt-5-mini
```

Options:
- `--username` / `--user-id` / `--all` – choose who to process (repeatable).
- `--comment-provider` / `--comment-model` / `--comment-batch-size` / `--comment-max-spend-usd` – forwarded to the comment insights LLM runner (defaults match `wb comment-llm`).
- `--glaze-model` and `--group-slug` – passed to the glazing step.
- `--dry-run` – plan comment batches only; skip LLM execution and glaze writes.

Under the hood the command calls `wb comment-llm` with `--user-id` filters (added for this workflow) so only the specified member’s comments are labeled before their snapshot + glaze run.

## Failure Handling & Runbook
- Guardrail violations or LLM errors automatically fall back to deterministic bios while recording the issue list inside each JSON output.
- Resume files make reruns idempotent; delete the resume file to force a full regeneration.
- Structured logs under `storage/` provide quick forensics (who ran, how long, dry-run vs write).
- If a highlight is missing or marked stale, the member/admin UIs fall back to the standard profile layout until the glaze job runs again.
- To reseed a highlight manually: `wb signal-profile glaze --user <id>` (or submit a manual override via `/admin/profiles/<id>`), then verify via `wb signal-profile freshness --user <id>`.
