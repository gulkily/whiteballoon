## Stage 1 – Cache model & migration plan
- Dependencies: Step 2 requirements; existing `users`/`user_attributes` schema.
- Changes: Define `InviteMapCache` SQLModel with `user_id` (unique FK), serialized payload (JSON/Text), `generated_at`, optional `version`/`ttl_seconds`, and helper indexes; outline migration using current schema tooling.
- Verification: Schema inspector detects new table; unit test ensuring model metadata lines up (e.g., round-trip create/read in temporary DB).
- Risks: Adding a new table requires DB migration coordination; payload column size choice (TEXT vs JSON) impacts portability.

## Stage 2 – Bidirectional 2-degree graph builder
- Dependencies: Stage 1 (data contract), existing `invite_graph_service` helpers.
- Changes: Extend service (or add companion helper) to: (a) walk downstream invitees breadth-first up to degree 2, (b) walk upstream chain by following `INVITED_BY_USER_ID` attributes up 2 hops, (c) return structured tree/dictionary that distinguishes `upstream` vs `downstream` lists with invite metadata.
- Verification: Unit tests covering: no inviter, single upstream chain, cycles/duplicate guards, and mixed branching with degree cap at 2; measure query count with naive fixtures to keep under target (<= number of visited nodes + 1 per level).
- Risks: Missing indices on `user_attributes` causing slow upstream lookups; accidentally including >2 degree nodes or duplicates when traversing shared invite paths.

## Stage 3 – Cache read/write/invalidation utilities
- Dependencies: Stage 1 table, Stage 2 data shape.
- Changes: Implement service functions to `get_cached_map(user_id)`, `store_cached_map(user_id, payload, version)`, `invalidate_cache(user_id)` plus TTL freshness check; serialize graph data (e.g., `json.dumps`) before storing.
- Verification: Unit tests ensuring cache hits return deserialized graphs, stale entries trigger rebuild, and invalidation deletes/updates rows; simulate concurrent rebuild to ensure upsert safety.
- Risks: Race conditions where simultaneous rebuilds clobber data; stale data persisting if invalidation misses a pathway.

## Stage 4 – UI route integration & template adjustments
- Dependencies: Stage 2 data format, Stage 3 cache helpers.
- Changes: Update `/invite/map` route to enforce 2-degree limit, consult cache prior to rebuild, and record render metrics; tweak `templates/invite/map.html` to show separate upstream/downstream sections (with empty states) and invite timestamps; add subtle loading/cached indicators if helpful.
- Verification: Manual smoke test navigating to Invite Map with/without cache, verifying layout across desktop/mobile widths; fastAPI test to ensure route returns 200 and includes expected DOM markers.
- Risks: Template complexity hurting readability; large payloads causing slow serialization despite cache hit.

## Stage 5 – Cache invalidation triggers
- Dependencies: Stage 3 invalidation API, knowledge of invite lifecycle.
- Changes: Hook invalidation into invite mutations: when a user sends a new invite (`create_invite_token`/send flow), when an invite is redeemed (`create_user_with_invite` writing `INVITED_BY_USER_ID`), and when invite-related attributes change via `user_attribute_service`; make sure both inviter and invitee cache entries are cleared because both graphs are affected.
- Verification: Unit tests or integration tests asserting cache rows disappear after these operations; manual scenario: user invites someone, reload map and confirm rebuild occurs.
- Risks: Missing an edge case (e.g., admin manually edits attributes) leaves stale cache; over-invalidation could thrash cache and negate benefits.

## Stage 6 – Documentation & rollout checklist
- Dependencies: Completion of Stages 1-5.
- Changes: Update relevant docs/README to mention social invite map + caching behavior, note TTL/invalidation policy; draft operational notes for clearing cache table if needed in production; summarize verification in Step 4 implementation summary.
- Verification: Documentation lint (spell-check/markdown preview if available) and manual checklists; final manual walkthrough of Invite Map with realistic seed data.
- Risks: Docs drifting from actual behavior; missing rollout steps for migrating existing data before deploying cache reliance.
