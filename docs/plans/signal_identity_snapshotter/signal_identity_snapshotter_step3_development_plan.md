# Signal Identity Snapshotter – Step 3 Development Plan

## Stage 1 – Snapshot schema + fixtures
- **Goal**: Define the canonical snapshot payload so downstream jobs share a stable contract.
- **Dependencies**: Step 2 feature description, Signal import metadata (`signal_member_key:*`).
- **Changes**: Create `SignalProfileSnapshot` dataclass (fields: `user_id`, `group_slug`, `message_count`, `first_seen_at`, `last_seen_at`, `top_links`, `top_tags`, `reaction_counts`, `attachment_counts`, `request_ids`). Document schema + JSON example in `docs/dev/signal_profile_snapshots.md` and add pytest fixtures.
- **Verification**: Unit test ensures dataclass serializes/deserializes cleanly; manual doc review.
- **Risks**: Field omissions could break later capabilities; mitigate via fixtures + doc review. Touches shared contract consumed by CLI + LLM generator.

## Stage 2 – Snapshot aggregation service
- **Goal**: Implement the query helper that builds snapshots from WB data.
- **Dependencies**: Stage 1 schema.
- **Changes**: Add `app/services/signal_profile_snapshot_service.py` with `build_snapshot(user_id: int, session: Session) -> SignalProfileSnapshot | None`. Query `UserAttribute` for Signal metadata, join `RequestComment`/attachments to compute counts, compile `top_links` (domain + count) and `top_tags` (from `comment_llm_insights_db`). Ensure idempotent results and caching of comment IDs.
- **Verification**: Unit tests with in-memory SQLite DB + seeded comments; confirm counts + timestamps match raw queries. Manual dry-run printing snapshot for HarvardStCommons sample.
- **Risks**: Expensive joins; mitigate via batched queries + indexes. Shared data contracts: uses canonical `request_comments` + `comment_llm_insights_db` APIs—no forks.

## Stage 3 – CLI + output writer
- **Goal**: Provide operators with a deterministic way to export snapshots.
- **Dependencies**: Stage 2 service.
- **Changes**: Extend `wb` CLI (new command `wb signal-profile snapshot`) that iterates user IDs (single or all), calls service, and writes JSON to `storage/signal_profiles/<user_id>.json`. Support `--dry-run`, summary stats, and logs.
- **Verification**: CLI integration test invoking command against fixture DB; manual run piping output to stdout and inspecting file contents.
- **Risks**: File permissions / path errors; mitigate with existing `storage` helpers. Command reuses CLI shell patterns; no new shared components.

## Stage 4 – Scheduling + observability
- **Goal**: Ensure snapshots stay fresh automatically.
- **Dependencies**: Stage 3 CLI.
- **Changes**: Add cron/systemd sample instructions plus optional background task registration inside existing scheduler module to run CLI nightly when `PROFILE_SIGNAL_GLAZE` enabled. Emit structured log lines + StatsD counters (`signal_glaze.snapshots_generated`).
- **Verification**: Manual test running scheduler stub; confirm logs + metrics fire.
- **Risks**: Cron misconfiguration; mitigated by docs. Scheduling touches shared ops docs only, no runtime API impact.
