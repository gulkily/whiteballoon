# Signal Profile Glaze – Stage 3 Implementation Playbook

The playbook turns each Stage 2 capability into bite-sized work packages (≤1 hr / ≤75 LOC), covering data contracts, instrumentation, verification, and fallback paths. Feature flag: `PROFILE_SIGNAL_GLAZE` (off by default) controls UI exposure + automated refresh jobs.

## 1. Signal Identity Snapshotter
**Goal**: Produce deterministic per-user “receipts” bundles for anyone tied to a Signal import.

### Work Packages
1. **Snapshot schema definition** – Add `SignalProfileSnapshot` dataclass + JSON schema (fields: `user_id`, `group_slug`, `message_count`, `first_seen_at`, `last_seen_at`, `top_links`, `top_tags`, `reaction_counts`, `attachment_counts`, `request_ids`). Document in `docs/dev/signal_profile_snapshots.md`. (≤40 LOC)
2. **Snapshot query helper** – New module `app/services/signal_profile_snapshot_service.py` that loads Signal-tagged `UserAttribute` rows, fetches related comments/attachments via SQL (batched), aggregates counts, and returns the dataclass. Ensure idempotence + caching per run. (≤70 LOC; unit tests hitting an in-memory DB).
3. **Extraction CLI** – Extend `wb` CLI with `wb signal-profile snapshot --user <id>|--all` hooking into the service, writing JSON snapshots to `storage/signal_profiles/<user_id>.json`. Provide `--dry-run` + summary counts. (≤60 LOC)
4. **Scheduler hook** – Add optional cron entry (docs + sample systemd timer) to run the CLI nightly; log runtime + number of refreshed snapshots to `signal_group_import.log`. (Docs-only + 10 LOC).

### Data/API Changes
- No DB migrations; outputs are JSON artifacts + in-memory responses from the service.
- Requires read access to `users`, `user_attributes`, `request_comments`, `comment_llm_insights_db` (for tags), and attachments metadata if available.

### Rollout / Ops
- Ship CLI + service hidden behind feature flag config (only run when `PROFILE_SIGNAL_GLAZE=1`).
- Document how to backfill snapshots for existing imports via `wb signal-profile snapshot --all` before enabling downstream jobs.
- Add structured logging (`logger.info("snapshot", user_id=?, message_count=? )`).

### Verification
- Unit tests for the service to confirm aggregation math + empty-case behavior.
- CLI integration test using fixture DB to ensure JSON output matches schema.
- Manual QA: run snapshotter against HarvardStCommons export, inspect JSON (spot-check counts vs DB queries).

### Fallback Plan
- If snapshotter fails, disable the cron + flag; downstream capabilities treat missing snapshots as “no data” and surface fallback copy.

## 2. Positivity-Tuned Bio Generator
**Goal**: Convert snapshots + LLM comment analyses into glorifying bios, proof points, and quotes while enforcing tone guardrails (bios can extend beyond 2–3 sentences when the user has rich chat history).

### Work Packages
1. **Prompt + rubric design** – Draft prompt template + tone checklist in `docs/prompts/signal_profile_glaze_prompt.md`. Include adjective palette, forbidden words, required sections, and rules for scaling length with available data (short when sparse, expansive when the user has deep chat history). Share for review before coding. (Docs only.)
2. **Generator module** – Implement `app/services/signal_profile_bio_service.py` with `generate_bio(snapshot, analyses)` returning `BioPayload`. Handles templating, fallback phrasing when data sparse, and normalizes proof points. (≤70 LOC.)
3. **LLM client wrapper** – Reuse comment-LLM config but add telemetry (provider/model). Add timeout/retry + structured logging of prompt hashes and response IDs for audits. (≤60 LOC.)
4. **Guardrail filter** – Post-process responses with regex + heuristic checks (length, positive tone). If violations found, auto-adjust copy via rule-based templates or flag for manual review (write fallback text). (≤50 LOC + tests.)
5. **Batch job command** – `wb signal-profile glaze --user/--all --dry-run` iterates snapshots, fetches most recent analyses from `comment_llm_insights_db`, and stores outputs via Capability 3 API. Collect metrics (bios generated, guardrail fallbacks). (≤70 LOC.)

### Data/API Changes
- Introduce `BioPayload` schema (bio text, proof points array, quotes array, provenance metadata).
- Needs read access to `comment_llm_insights_db` tables (`analyses`) and snapshots from Capability 1.
- Writes go through Capability 3 storage layer (no direct DB writes here).

### Rollout / Ops
- Hide LLM job behind `PROFILE_SIGNAL_GLAZE` flag + `SIGNAL_PROFILE_GLAZE_MODEL` env var.
- Provide dry-run option logging prompts/responses without storing.
- Instrument job with metrics: bios attempted, success, guardrail-failed, LLM errors. Emit to structured log + optional StatsD.

### Verification
- Unit tests for `signal_profile_bio_service` using fixture snapshots to assert positive wording + inclusion of references.
- Snapshot-based golden tests for prompt -> response scaffolding (mock LLM client).
- Manual QA: run glaze job on a subset; content review by ops to ensure tone matches expectation before enabling auto-rollout.

### Fallback Plan
- If LLM provider unavailable or guardrail fails repeatedly, job exits early and logs entries as “pending manual copy”; UI will show baseline snapshot stats instead of bios.

## 3. Profile Insight Store & Freshness Manager
**Goal**: Persist bios/proof points safely, track provenance, and kick off refreshes when data changes.

### Work Packages
1. **Schema migration** – Add `user_profile_highlights` table (`user_id` PK, `bio_text`, `proof_points_json`, `quotes_json`, `source_group`, `snapshot_hash`, `llm_model`, `generated_at`, `stale_after`, `manual_override`, `override_text`). Migration via Alembic script + SQLModel model. (≤70 LOC SQL + model.)
2. **Data access layer** – Create `app/services/user_profile_highlight_service.py` with CRUD helpers (`get`, `upsert_auto`, `set_manual_override`, `mark_stale`). Include transaction + optimistic locking via snapshot hash. (≤65 LOC + tests.)
3. **Freshness detector** – Background task (FastAPI startup or separate CLI) that watches `request_comments` for Signal-tagged requests; when new comments exist beyond stored `last_message_at`, mark highlight stale. Also expire entries based on `stale_after`. (≤70 LOC.)
4. **Operator tooling** – Admin route `/admin/profiles/{id}/glaze` to show stored payload, provenance, regen button, and manual override textarea. Wire regen button to Capability 2 job via task queue/command. (≤75 LOC across route + template.)
5. **Audit logging** – Log every write/override with actor ID + diff into existing admin audit log or new table. (≤40 LOC.)

### Data/API Changes
- New DB table + SQLModel.
- Service exposes read/write API consumed by CLI + UI.
- Need background job scheduler (reuse existing Celery/async tasks or simple APScheduler) to execute freshness check.

### Rollout / Ops
- Ship migration but keep flag off until data populated.
- Provide backfill command `wb signal-profile store-backfill --from-snapshots` to migrate existing JSON/LLM outputs if any.
- Document manual override workflow + how to clear staleness.
- Add metrics: count of fresh/stale highlights, overrides in place.

### Verification
- Migration tested locally + CI (apply/rollback).
- Unit tests for service (insert/upsert, override locking, stale detection).
- Integration test hitting admin route to ensure perms + overrides persist.
- Manual QA: simulate new Signal message, confirm freshness job marks stale and UI shows “needs refresh”.

### Fallback Plan
- If migration causes issues, rollback table (no other systems depend yet). Highlight reads will fallback to “no highlight” messaging.
- Manual override flag ensures we can freeze bios if automation misbehaves.

## 4. Glazed Profile Presentation
**Goal**: Surface the celebratory bios + proof points in `/profile` + `/admin/profiles`, with provenance and CTAs.

### Work Packages
1. **API wiring** – Extend existing profile route dependencies to fetch highlight payloads via Capability 3 service (only when flag on) and inject into template context. (≤50 LOC).
2. **Member UI block** – Update `templates/profile/show.html` with a “Community perception” card: glazed bio paragraphs, proof point pills linking to requests/URLs, freshness chip (“Updated Mar 19, 2024”). Add fallback note when highlight missing. (≤60 LOC HTML/CSS).
3. **Admin view enhancements** – On `/admin/profiles/{id}`, add new panel summarizing snapshot stats, stored bio, guardrail status, and regen/override controls (hooked to Capability 3 route). (≤70 LOC template + JS for async trigger).
4. **Receipts links** – Build helper to extract `top_links` from snapshot/highlight and render as list with domain label + outbound icon. Each link uses `rel="noopener"` and click tracking data attributes. (≤40 LOC).
5. **Instrumentation** – Add client-side event hook (simple POST to `/api/metrics`) recording profile view + “proof point clicked”. Wire to existing analytics logger. (≤40 LOC JS/backend.)
6. **Feature flag gating + perms** – Ensure block only renders for authenticated members (or admins). Add unit tests verifying unauthorized sessions never see Signal data. (≤30 LOC + tests.)

### Data/API Changes
- Profile routes now depend on highlight service; ensure caching to avoid N+1 queries.
- Admin routes gain POST endpoint for regen/manual override actions.

### Rollout / Ops
- Enable `PROFILE_SIGNAL_GLAZE` in staging, confirm UI with seeded HarvardStCommons data before prod.
- Provide design QA checklist (tone, layout, accessibility). Ensure microcopy reviewed.
- Monitor analytics for profile view volume + click-through to proof points.

### Verification
- Template tests (pytest + Jinja) verifying block renders for flagged user, hides otherwise.
- Cypress/Playwright smoke tests for profile page to ensure cards load and CTA works.
- Manual QA: review a few users’ pages to ensure links resolve and bios sound celebratory.

### Fallback Plan
- Toggle flag off to hide UI instantly if content questionable.
- Provide manual link in admin to view raw snapshots even if glaze hidden, for debugging.

## Global Verification & Rollout Checklist
- [ ] Run snapshot backfill, then glaze generator dry-run, review output with ops.
- [ ] Apply migration + deploy services with flag off.
- [ ] Enable flag in staging, run glaze job, confirm UI + analytics.
- [ ] Announce operator workflow (overrides, regen) and document SOP.
- [ ] Gradually enable flag for subset of members before full rollout.

## Instrumentation & Monitoring
- Structured logs for each capability (snapshot, glaze job, highlight store, UI view).
- Metrics counters: `signal_glaze.snapshots_generated`, `signal_glaze.bios_generated`, `signal_glaze.guardrail_failures`, `signal_glaze.highlights_stale`, `signal_glaze.profile_views`.
- Alerts: guardrail failure rate >10% over 30 min, freshness backlog >50 stale entries, UI errors when loading highlights.

## Policy / Risk Follow-Ups
- Finalize guidance on multi-group personas and misrepresentation limits before auto-rollout.
- Decide on automatic regeneration when prompt template changes (hash stored in highlight table; changes trigger regen job).
- Review data retention (ensure Signal quotes/links comply with privacy commitments).
