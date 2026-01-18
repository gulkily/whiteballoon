# Profile Insight Store & Freshness Manager – Step 3 Development Plan

## Stage 1 – Schema + model design
- **Goal**: Introduce persistence for bios/proof points with provenance.
- **Dependencies**: Highlight requirements from Stage 2/3 docs.
- **Changes**: Draft `user_profile_highlights` table spec (columns: `user_id` PK, `bio_text`, `proof_points_json`, `quotes_json`, `source_group`, `snapshot_hash`, `llm_model`, `generated_at`, `stale_after`, `manual_override`, `override_text`). Add SQLModel class and Alembic migration (conceptual description only here).
- **Verification**: Manual schema review + ensure naming aligns with existing tables.
- **Risks**: Schema bloat; mitigate by keeping JSON columns for flexible payloads.

## Stage 2 – Service layer
- **Goal**: Provide safe CRUD API over highlights.
- **Dependencies**: Stage 1 schema.
- **Changes**: Implement `app/services/user_profile_highlight_service.py` with methods:
  - `get(user_id: int) -> Highlight | None`
  - `upsert_auto(payload: BioPayload, snapshot_hash: str, metadata: HighlightMeta) -> Highlight`
  - `set_manual_override(user_id: int, text: str)`
  - `mark_stale(user_id: int, reason: str)`
  Ensure transactions + optimistic locking via `snapshot_hash`.
- **Verification**: Unit tests hitting SQLite DB to cover insert/update/override/stale flows.
- **Risks**: Race conditions when concurrent jobs update same user; locking + hash mitigate.

## Stage 3 – Freshness detector job
- **Goal**: Flag bios needing regeneration.
- **Dependencies**: Stage 2 service, Signal request IDs mapping.
- **Changes**: Background task or CLI `wb signal-profile freshness-scan` that checks for new Signal comments after `generated_at` or after `stale_after` threshold, marking highlights stale and enqueueing regen (write to queue or log). Hook into scheduler.
- **Verification**: Tests using fake timestamps; manual run adding new comment and confirming stale flag flips.
- **Risks**: Long scans; mitigate via incremental checkpoints.

## Stage 4 – Admin tooling + audit log
- **Goal**: Empower operators to inspect/override highlights.
- **Dependencies**: Stage 2 service, existing admin profiles route.
- **Changes**: Add `/admin/profiles/{id}/glaze` panel showing stored highlight, staleness, provenance, and controls to regenerate (trigger CLI) or lock manual override. Log actions via existing admin audit log (record actor, timestamp, diff).
- **Verification**: Manual QA in admin UI + unit tests verifying permission checks.
- **Risks**: Unauthorized edits; ensure route requires admin role and logs all changes.

## Stage 5 – Monitoring + fallback semantics
- **Goal**: Ensure system reliability and graceful degradation.
- **Dependencies**: Stages 2–4 complete.
- **Changes**: Add metrics for count of fresh/stale highlights, overrides, regen queue depth. Document fallback behavior (if highlight missing or stale, UI shows snapshot stats). Provide runbook entry for reseeding table.
- **Verification**: Manual metrics inspection; runbook review.
- **Risks**: Metrics flood; keep counters low-cardinality.
