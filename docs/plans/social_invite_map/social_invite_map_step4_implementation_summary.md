# Social Invite Map – Implementation Summary

## Stage 1 – Cache model & migration plan
- Changes: Added `InviteMapCache` SQLModel (text payload, version, generated_at) in `app/models.py` and created a basic model round-trip test to confirm schema creation.
- Verification: `tests/models/test_invite_map_cache.py` ensures the table can be created in-memory and stores JSON payloads.

## Stage 2 – Bidirectional 2-degree graph builder
- Changes: Added upstream ancestor + invite map dataclasses and `build_bidirectional_invite_map` helper in `app/services/invite_graph_service.py`, ensuring 2-degree traversal in both directions with cycle guards.
- Verification: Extended `tests/services/test_invite_graph_service.py` to cover upstream/downstream assembly and confirm cycle protection.

## Stage 3 – Cache read/write/invalidation utilities
- Changes: Introduced `app/services/invite_map_cache_service.py` with TTL-aware read/write helpers plus serialization/deserialization support in `invite_graph_service`.
- Verification: Added `tests/services/test_invite_map_cache_service.py` covering round-trip storage, TTL expiry, and invalidation.

## Stage 4 – UI route integration & template adjustments
- Changes: `/invite/map` now reads from the cache service, rebuilds bidirectional graphs when necessary, and renders a single outline-style tree that links upstream and downstream nodes with connective lines plus a cache-hit indicator. Upstream inviters now show their other invitees ("sisters"/"grandsisters") directly off the same branch, every username links to `/people/{username}`, the viewer’s node gets a bold highlight ring, and each node surfaces the member’s profile photo (or initial fallback) pulled from stored attributes.
- Verification: Manual browser snapshot (dev server) and spot-checked via existing service tests; route-level pytest intentionally skipped per request.

## Stage 5 – Cache invalidation triggers
- Changes: `user_attribute_service.set_attribute` now clears cached maps whenever `invited_by_user_id` changes, covering invite acceptance and admin edits; invalidates both inviter and invitee entries.
- Verification: Exercised via existing unit tests for attribute helper indirectly; manual registration walkthrough recommended (not yet run per testing constraints).

## Stage 6 – Documentation & rollout checklist
- Pending
